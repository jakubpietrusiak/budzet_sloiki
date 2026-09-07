import io
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from database import get_db_connection

class NumberedCanvas(canvas.Canvas):
    """Automatyczne numerowanie stron w stopce PDF"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawRightString(A4[0] - 40, 30, f"Strona {self._pageNumber} z {page_count}")
        self.drawString(40, 30, f"Fit HERO Engine — Raport Analizy Treningowej PDF | Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

def generate_fit_hero_pdf_report(plan_id=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=50
    )
    
    story = []
    styles = getSampleStyleSheet()

    # Własne style dla raportu
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=colors.HexColor("#0f172a"), spaceAfter=10)
    h2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=colors.HexColor("#0284c7"), spaceBefore=14, spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor("#334155"))
    bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    prompt_style = ParagraphStyle('PromptBody', parent=body_style, fontName='Helvetica-Oblique', fontSize=8.5, leading=11, textColor=colors.HexColor("#1e293b"))

    # POBIERANIE DANYCH Z BAZY
    conn = get_db_connection()
    df_body = pd.read_sql_query("SELECT * FROM fit_body_params ORDER BY entry_date DESC", conn)
    df_goals = pd.read_sql_query("SELECT * FROM fit_target_goals", conn)
    goals = dict(zip(df_goals['param_key'], df_goals['target_val'])) if not df_goals.empty else {}
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    df_sessions = pd.read_sql_query("SELECT * FROM fit_workout_sessions WHERE workout_date >= ? ORDER BY workout_date DESC", conn, params=(thirty_days_ago,))
    df_logs = pd.read_sql_query("SELECT * FROM fit_workout_logs WHERE workout_date >= ? ORDER BY workout_date DESC", conn, params=(thirty_days_ago,))
    
    # Wybór planu
    if plan_id:
        df_plans = pd.read_sql_query("SELECT * FROM fit_plans WHERE id = ?", conn, params=(plan_id,))
        df_exercises = pd.read_sql_query("SELECT * FROM fit_plan_exercises WHERE plan_id = ?", conn, params=(plan_id,))
    else:
        df_plans = pd.read_sql_query("SELECT * FROM fit_plans LIMIT 1", conn)
        selected_id = df_plans.iloc[0]['id'] if not df_plans.empty else None
        df_exercises = pd.read_sql_query("SELECT * FROM fit_plan_exercises WHERE plan_id = ?", conn, params=(selected_id,)) if selected_id else pd.DataFrame()

    conn.close()

    # 1. NAGŁÓWEK DOKUMENTU
    story.append(Paragraph("💪 Fit HERO Engine — Raport Analizy Planu i Postępów", title_style))
    story.append(Paragraph("Dokument wygenerowany automatycznie dla modułu analitycznego AI. Zawiera kompletne dane bioimpedancji, obwodów ciała, struktury planu oraz historii RPE/zmęczenia z ostatnich 30 dni.", body_style))
    story.append(Spacer(1, 10))

    # 2. PROFIL UŻYTKOWNIKA & CELE
    story.append(Paragraph("1. METADANE UŻYTKOWNIKA & PROFIL ADAPTACJI", h2_style))
    latest_row = df_body.iloc[0] if not df_body.empty else {}
    
    meta_data = [
        [Paragraph("<b>Wzrost:</b> 186 cm", body_style), Paragraph(f"<b>Aktualna Masa:</b> {latest_row.get('weight_kg', '--')} kg", body_style), Paragraph(f"<b>Profil Adaptacji:</b> {goals.get('posture_profile', 'recomp').upper()}", body_style)],
        [Paragraph(f"<b>Cel Waga:</b> {goals.get('weight_kg', '--')} kg", body_style), Paragraph(f"<b>Cel Pas:</b> {goals.get('waist_cm', '--')} cm", body_style), Paragraph(f"<b>Cel Klatka:</b> {goals.get('chest_cm', '--')} cm", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[170, 170, 180])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # 3. KARTA POMIARÓW & SYLWETKA
    story.append(Paragraph("2. KARTA POMIAROWA SYLWETKI & BIOIMPEDANCJA XIAOMI", h2_style))
    if not df_body.empty:
        first_row = df_body.iloc[-1]
        body_table_data = [
            [Paragraph("<b>Parametr</b>", bold_body), Paragraph("<b>Start (A)</b>", bold_body), Paragraph("<b>Aktualnie (B)</b>", bold_body), Paragraph("<b>Delta</b>", bold_body)]
        ]
        params_map = [
            ("Masa Ciała (kg)", "weight_kg"), ("Tkanka Tłuszczowa (%)", "body_fat_pct"),
            ("Czysta Masa LBM (kg)", "lbm_kg"), ("Obwód Pasa (cm)", "waist_cm"),
            ("Obwód Klatki (cm)", "chest_cm"), ("Biceps (cm)", "biceps_cm")
        ]
        for name, key in params_map:
            val_a = first_row.get(key)
            val_b = latest_row.get(key)
            diff_str = f"{(val_b - val_a):+.1f}" if (val_a is not None and val_b is not None) else "--"
            body_table_data.append([
                Paragraph(name, body_style),
                Paragraph(f"{val_a:.1f}" if val_a else "--", body_style),
                Paragraph(f"{val_b:.1f}" if val_b else "--", body_style),
                Paragraph(diff_str, bold_body)
            ])
        t_body = Table(body_table_data, colWidths=[200, 100, 100, 120])
        t_body.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_body)
    story.append(Spacer(1, 10))

    # 4. AKTUALNY PLAN TRENINGOWY
    plan_name = df_plans.iloc[0]['plan_name'] if not df_plans.empty else "Brak Planu"
    story.append(Paragraph(f"3. STRUKTURA PLANU TRENINGOWEGO: {plan_name.upper()}", h2_style))
    if not df_exercises.empty:
        ex_table_data = [
            [Paragraph("<b>Ćwiczenie</b>", bold_body), Paragraph("<b>Obciążenie</b>", bold_body), Paragraph("<b>Serie</b>", bold_body), Paragraph("<b>Zakres Powtórzeń</b>", bold_body), Paragraph("<b>Ciężar Domyślny</b>", bold_body)]
        ]
        for _, r in df_exercises.iterrows():
            ex_table_data.append([
                Paragraph(r['exercise_name'], body_style),
                Paragraph(r.get('load_type', 'Ciężar (kg)'), body_style),
                Paragraph(str(r['target_sets']), body_style),
                Paragraph(str(r['target_reps']), body_style),
                Paragraph(f"{r.get('default_weight_kg', 0)} kg", body_style)
            ])
        t_ex = Table(ex_table_data, colWidths=[170, 100, 60, 100, 90])
        t_ex.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e0f2fe")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#bae6fd")),
            ('ALIGN', (2,0), (-1,-1), 'CENTER'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_ex)
    story.append(Spacer(1, 10))

    # 5. EXECUTION & LOGI Z TRZYDZIESTU DNI (RPE / FATIGUE)
    story.append(Paragraph("4. HISTORIA REALIZACJI & SAMOOCENA ZMĘCZENIA (30 DNI)", h2_style))
    if not df_sessions.empty:
        avg_completion = df_sessions['completion_pct'].mean()
        actual_count = len(df_sessions)
        avg_rpe = df_logs['rpe_score'].dropna().mean() if not df_logs.empty and 'rpe_score' in df_logs.columns else 0.0
        
        stat_text = f"<b>Zrealizowane Sesje:</b> {actual_count} sesji w miesiącu | <b>Średnia Wykonania Planu:</b> {avg_completion:.1f}% | <b>Średnie RPE:</b> {avg_rpe:.1f} / 4.0"
        story.append(Paragraph(stat_text, body_style))
        story.append(Spacer(1, 6))

    # 6. GOTOWY PROMPT DLA AI
    story.append(KeepTogether([
        Paragraph("5. DEDYKOWANE POLECENIE DLA ANALIZATORA AI (SYSTEM PROMPT)", h2_style),
        Table([
            [Paragraph(
                "<b>Wklej poniższy tekst do modelu AI razem z tym dokumentem:</b><br/><br/>"
                "<i>\"Jesteś doświadczonym trenerem personalnym oraz specjalistą ds. biomechaniki i rekompozycji sylwetkowej. "
                "Przeanalizuj powyższy raport PDF dla mężczyzny o wzroście 186 cm. Uwzględnij jego profil adaptacji, zmiany wagi/obwodów, "
                "strukturę planu oraz odnotowane poziomy RPE i zmęczenia z ostatnich 30 dni. "
                "Zidentyfikuj ewentualne wąskie gardła (np. za mała/za duża objętość, brak priorytetu dla klatki/barków pod V-Taper, "
                "złe zarządzanie RPE) i zaproponuj konkretne, punktowe korekty w serii, powtórzeniach oraz doborze ćwiczeń.\"</i>",
                prompt_style
            )]
        ], colWidths=[520], style=[
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
            ('PADDING', (0,0), (-1,-1), 10),
        ])
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer