import os
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

base_dir = Path(r"c:\Users\alan\Downloads\govsim_handoff_2026-11-08\govsim_handoff")
template_path = base_dir / "Cópia de Apart Research hackathon submission template.docx"
output_docx_path = base_dir / "Submissao_Apart_Research_GovSim_Evolucao_Normas_PT.docx"

doc = Document(str(template_path))

# Clear all paragraphs and tables from the template
for p in list(doc.paragraphs):
    p._element.getparent().remove(p._element)
for t in list(doc.tables):
    t._element.getparent().remove(t._element)

def set_run(run, font_name="Arial", size_pt=10.5, bold=False, italic=False, color_rgb=(0,0,0)):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(*color_rgb)

def add_p(text="", align=WD_ALIGN_PARAGRAPH.LEFT, space_before=2, space_after=6, line_spacing=1.15):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        run = p.add_run(text)
        set_run(run, size_pt=10.5)
    return p

def add_heading(text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        set_run(run, size_pt=14, bold=True, color_rgb=(10, 40, 90))
    elif level == 2:
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(text)
        set_run(run, size_pt=12, bold=True, color_rgb=(30, 60, 110))
    elif level == 3:
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(text)
        set_run(run, size_pt=11, bold=True, italic=True, color_rgb=(50, 50, 50))
    return p

# --- TÍTULO & AUTORES ---
p_title = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=6)
r_title = p_title.add_run("Tempo até o Colapso e Governança Emergente:\nComo Desertores Gananciosos Desestabilizam a Evolução de Normas em Bens Comuns de LLMs")
set_run(r_title, size_pt=17, bold=True, color_rgb=(15, 34, 64))

p_auth = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=4, space_after=4)
r_a1 = p_auth.add_run("[Nome do Autor 1]")
set_run(r_a1, size_pt=11, bold=True)
r_aff1 = p_auth.add_run(" ([Filiação / Instituição 1])       ")
set_run(r_aff1, size_pt=10, italic=True)
r_a2 = p_auth.add_run("[Nome do Autor 2]")
set_run(r_a2, size_pt=11, bold=True)
r_aff2 = p_auth.add_run(" ([Filiação / Instituição 2])\n")
set_run(r_aff2, size_pt=10, italic=True)
r_conf = p_auth.add_run("Swarm Alignment Hackathon — Apart Research (Novembro de 2026)")
set_run(r_conf, size_pt=9.5, italic=True, color_rgb=(100, 100, 100))

# --- RESUMO (ABSTRACT BOX) ---
tbl_abs = doc.add_table(rows=1, cols=1)
tbl_abs.alignment = WD_TABLE_ALIGNMENT.CENTER
cell_abs = tbl_abs.rows[0].cells[0]
cell_abs.width = Inches(6.5)
shd = parse_xml(r'<w:shd {} w:fill="F4F6F9"/>'.format(nsdecls('w')))
cell_abs._tc.get_or_add_tcPr().append(shd)
borders = parse_xml(r'''
    <w:tcBorders {} >
        <w:top w:val="single" w:sz="6" w:space="0" w:color="0072B2"/>
        <w:left w:val="single" w:sz="18" w:space="0" w:color="0072B2"/>
        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="0072B2"/>
        <w:right w:val="single" w:sz="6" w:space="0" w:color="0072B2"/>
    </w:tcBorders>'''.format(nsdecls('w')))
cell_abs._tc.get_or_add_tcPr().append(borders)

p_abs_title = cell_abs.paragraphs[0]
p_abs_title.paragraph_format.space_before = Pt(4)
p_abs_title.paragraph_format.space_after = Pt(3)
r_at = p_abs_title.add_run("Resumo")
set_run(r_at, size_pt=11, bold=True, color_rgb=(0, 114, 178))

p_abs_body = cell_abs.add_paragraph()
p_abs_body.paragraph_format.space_before = Pt(0)
p_abs_body.paragraph_format.space_after = Pt(4)
p_abs_body.paragraph_format.line_spacing = 1.15
abstract_text_pt = (
    "À medida que sistemas descentralizados multiagente baseados em LLMs são progressivamente implementados em ambientes de recursos "
    "compartilhados e finitos, a capacidade de estabelecer e sustentar governança coletiva torna-se imperativa para o alinhamento de enxames "
    "(swarm alignment). Avaliando a gestão de bens comuns sob tomada de decisão simultânea, investigamos como enxames cooperativos de LLMs governam "
    "recursos compartilhados e respondem à intrusão abrupta de um agente recém-chegado (newcomer) não alinhado e predatório. Replicando o arcabouço "
    "pesqueiro GovSim com um modelo de pesos abertos (qwen2.5:7b, 40 simulações concluídas ao longo de 15 sementes), demonstramos que a comunicação "
    "aliada a prompts de universalização sustenta os bens comuns ao longo de horizontes de 12 meses. A introdução de um agente ganancioso no Mês 4 "
    "reduz bruscamente a sobrevivência coletiva: a sobrevivência no marco temporal cai de 88% nos controles para 33% (teste exato de Fisher p = 0,028). "
    "Crucialmente, a degradação ocorre sem contágio comportamental: os agentes incumbentes não copiam a extração predatória, reduzindo as toneladas solicitadas. "
    "Expandindo além da exaustão física, revelamos um mecanismo institucional inédito: enxames cooperativos exibem espontaneamente aperto normativo adaptativo "
    "(Princípio 2 de Elinor Ostrom), reduzindo progressivamente os limites por agente de 10 para 1–4 t/mês para construir uma margem de segurança ecológica. "
    "O desertor quebra essa convergência, forçando os enxames sobreviventes à inflação de normas (slopes revertendo de -0,24 para +0,68 t/mês, p = 0,006). "
    "Esses resultados provam que o alinhamento em enxames não falha por trapaça interna, mas pela destruição do capital institucional acumulado."
)
r_ab = p_abs_body.add_run(abstract_text_pt)
set_run(r_ab, size_pt=9.5, italic=False)

add_p("", space_after=6)

# --- 1. INTRODUÇÃO ---
add_heading("1. Introdução", 1)
p_intro = add_p()
p_intro.add_run(
    "Uma questão fundamental no alinhamento de enxames (swarm alignment) consiste em determinar se agentes autônomos de IA, "
    "operando em redes abertas e descentralizadas, conseguem estabelecer normas sociais duradouras para prevenir o esgotamento catastrófico "
    "de recursos compartilhados (a Tragédia dos Comuns). Enquanto o alinhamento de agentes individuais enfatiza a obediência a instruções "
    "e a inofensividade, o alinhamento multiagente introduz fenômenos em nível macro: coordenação na teoria dos jogos, credibilidade na comunicação, "
    "pressão social entre pares e resiliência institucional contra agentes oportunistas não alinhados (Dafoe et al., 2020; Park et al., 2023)."
)
p_intro2 = add_p()
p_intro2.add_run(
    "Um modelo central de ameaça em enxames autônomos reside na dinâmica da 'maçã podre' (bad apple): um grupo de agentes cooperativos e comunicativos "
    "consegue resistir à infiltração súbita de um desertor focado na maximização de retorno imediato? Caso os agentes incumbentes copiem prontamente o "
    "comportamento predatório (contágio comportamental), a coesão social colapsa de imediato. Por outro lado, caso os incumbentes mantenham a adesão aos "
    "acordos coletivos, a questão estrutural passa a ser se os mecanismos descentralizados de governança possuem capacidade adaptativa suficiente para "
    "absorver choques exógenos de deserção."
)
p_intro3 = add_p()
p_intro3.add_run(
    "Neste trabalho, realizamos uma avaliação empírica aprofundada utilizando o ambiente GovSim (Piatti et al., 2024), avaliando um modelo de pesos "
    "abertos de 7 bilhões de parâmetros (Qwen 2.5 7B) em 40 simulações de longo horizonte. Nossas contribuições principais são:\n"
)
bullet1 = add_p(space_before=1, space_after=2)
r_b1 = bullet1.add_run("1. Replicação em Pesos Abertos e Robustez de Benchmark: ")
set_run(r_b1, bold=True)
bullet1.add_run("Demonstramos que prompts de universalização combinados com diálogo mensal em linguagem natural sustentam recursos comuns em modelos locais abertos (Qwen 2.5 7B), atingindo 54% de sobrevivência em 12 meses contra 0% no baseline sem comunicação (p = 5,4e-6).")

bullet2 = add_p(space_before=1, space_after=2)
r_b2 = bullet2.add_run("2. Impacto do Marco Temporal da Infiltração Gananciosa: ")
set_run(r_b2, bold=True)
bullet2.add_run("Por meio de uma análise de sobrevivência com marco no Mês 4 (início da pesca do newcomer), isolamos o efeito do agente ganancioso de distorções pré-tratamento no tamanho do grupo. O desertor provoca uma queda acentuada na sobrevida até o Mês 12 (33% vs 88%, teste exato de Fisher p = 0,028; log-rank do marco p = 0,024).")

bullet3 = add_p(space_before=1, space_after=2)
r_b3 = bullet3.add_run("3. Ausência de Contágio Comportamental: ")
set_run(r_b3, bold=True)
bullet3.add_run("Testamos se os incumbentes escalam seus pedidos de pesca após a entrada do desertor. Ao contrário do previsto por modelos tradicionais de contágio, os incumbentes pediram menos peixes após a chegada (mudança mediana de -1,5t vs -3,7t nos controles, p = 0,16). Retratando métricas anteriores de razão artefatual, demonstramos que os incumbentes mantêm autocontenção.")

bullet4 = add_p(space_before=1, space_after=4)
r_b4 = bullet4.add_run("4. Evolução Emergente de Normas (Paradigma de Ostrom): ")
set_run(r_b4, bold=True)
bullet4.add_run("Introduzimos uma análise institucional inédita rastreando os limites negociados. Enxames cooperativos desenvolvem espontaneamente aperto normativo adaptativo (Ostrom, 1990), reduzindo os tetos de 10 para 1–4 t/agente para criar margem de segurança. O desertor corrompe esse pacto, revertendo a dinâmica em inflação de normas (+0,68 t/mês, p = 0,006).")

# --- 2. TRABALHOS RELACIONADOS ---
add_heading("2. Trabalhos Relacionados", 1)
p_rw = add_p()
p_rw.add_run(
    "Alinhamento Multiagente e Dilemas Sociais: A coordenação entre agentes autônomos tem sido investigada historicamente no aprendizado por "
    "reforço multiagente (Leibo et al., 2017) e na teoria dos jogos. Em enxames de LLMs, Park et al. (2023) exibiram dinâmicas sociais verossímeis, "
    "enquanto Mekhalfi et al. (2024) exploraram falhas de coordenação em jogos matriciais. Todavia, a durabilidade institucional perante desertores "
    "adversariais permaneceu pouco explorada.\n\n"
    "GovSim e Governança em Linguagem Natural: Piatti et al. (2024) introduziram o GovSim para avaliar LLMs em dilemas de recursos comuns, constatando "
    "que modelos sem instrução específica colapsam rapidamente os ecossistemas, ao passo que prompts de universalização (fundamentação ética kantiana) "
    "habilitam cooperação duradoura no GPT-4. Expandimos o GovSim aplicando modelos abertos locais e executando o primeiro mapeamento longitudinal de normas.\n\n"
    "Economia Institucional de Ostrom: Elinor Ostrom (1990) formulou oito princípios centrais de design para a gestão sustentável de bens comuns, "
    "demonstrando empiricamente que comunidades bem-sucedidas adaptam progressivamente as regras de apropriação às condições ecológicas locais. "
    "Conectamos a segurança de IA à economia institucional ao avaliar se enxames de LLMs manifestam espontaneamente governança adaptativa estilo Ostrom."
)

# --- 3. METODOLOGIA ---
add_heading("3. Metodologia", 1)
p_m1 = add_p()
p_m1.add_run(
    "Especificação do Ambiente: Empregamos o cenário pesqueiro do GovSim (fishing_v7.0, commit 1d11adf). O bem comum consiste em um lago com capacidade "
    "de suporte C_max = 100 toneladas. No início de cada mês, a biomassa dobra, limitada a 100t. Cada agente submete privadamente uma solicitação de captura "
    "(wanted_resource). Havendo demanda total superior à disponível, a colheita é distribuída estocasticamente de forma proporcional. O colapso do recurso "
    "é definido como pool < 5 toneladas pós-pesca. O horizonte temporal é de 12 meses (rodadas 0 a 11)."
)
p_m2 = add_p()
p_m2.add_run(
    "Condições Experimentais e Modelo de Ameaça:\n"
    "• Baseline (fish_baseline_concurrent): 5 agentes decidem colheitas simultâneas sem qualquer canal de diálogo.\n"
    "• Universalization (fish_baseline_concurrent_universalization): 5 agentes realizam assembleia mensal em linguagem natural antes da pesca, estimulados "
    "por raciocínio de universalização ('E se todos pescassem essa quantia?'). Ao término, acordam um teto individual (conversation_resource_limit) em vigor no mês seguinte.\n"
    "• Newcomer Perturbation (fish_perturbation_outsider_universalization): As rodadas 0–2 iniciam com 4 incumbentes cooperativos sob universalização. "
    "Na rodada 3 (início do Mês 4), um 5º agente ('Luke', persona_4) é introduzido com prompt egoísta que instrui maximização unilateral de lucro imediato."
)
p_m3 = add_p()
p_m3.add_run(
    "Modelo e Execução Computacional: Todas as simulações rodaram localmente com o Qwen 2.5 7B (qwen2.5:7b) via Ollama (backend ROCm, GPU AMD RX 6650 XT). "
    "A temperatura de amostragem foi fixada em 0,7 para introduzir dispersão estocástica realista entre sementes (1 a 15). As condições foram intercaladas por semente. "
    "O esforço computacional somou 871 minutos de execução (~14,5 horas) para 40 runs finalizados (14 baseline, 13 universalization, 13 newcomer)."
)
p_m4 = add_p()
p_m4.add_run(
    "Métricas Estatísticas e de Sobrevivência: Ajustamos curvas de Kaplan-Meier com intervalos de confiança de 95%, testes log-rank com correção de Holm e "
    "Tempo Médio de Sobrevivência Restrito (RMST) em 12 meses. Para isolar o efeito do newcomer, aplicamos Análise de Sobrevivência de Marco (Landmark Analysis) "
    "no Mês 4. Para dinâmica de normas, ajustamos regressões lineares sobre os limites mensais obtendo a taxa de aperto (slope) e calculamos a taxa de conformidade "
    "(fração de capturas estritamente dentro do limite acordado)."
)

# --- 4. RESULTADOS ---
add_heading("4. Resultados", 1)

add_heading("4.1 Baseline vs. Universalization (Replicação)", 2)
p_r1 = add_p()
p_r1.add_run(
    "Agentes baseline sem comunicação esgotam a pescaria no primeiro mês: todos os 14 runs colapsaram no Mês 1 (mediana de 1,0 mês; RMST de 1,07 meses). "
    "Em contrapartida, a universalização viabilizou cooperação sustentável: 7 de 13 runs (54%) alcançaram o horizonte integral de 12 meses "
    "(RMST de 7,62 meses, log-rank vs baseline p = 5,4e-6, Tabela 1). Isso valida a replicação de Piatti et al. (2024) em modelo aberto local de 7B."
)

# Tabela 1: Sobrevivência Geral
tbl_s = doc.add_table(rows=4, cols=6)
tbl_s.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Condição", "Runs (n)", "Colapsos", "Sobrevida Mediana", "RMST (12 meses)", "S(12 Meses)"]
data_s = [
    ["Baseline", "14", "14 (100%)", "1,0 mês", "1,07 ± 0,26", "0,00"],
    ["Universalization", "13", "6 (46%)", "Não atingida", "7,62 ± 1,32", "0,54"],
    ["Newcomer Univ", "13", "9 (69%)", "5,0 meses", "6,77 ± 1,01", "0,31"]
]
for i, h in enumerate(headers):
    cell = tbl_s.rows[0].cells[i]
    cell.paragraphs[0].text = h
    set_run(cell.paragraphs[0].runs[0], size_pt=9.5, bold=True, color_rgb=(255,255,255))
    shd = parse_xml(r'<w:shd {} w:fill="0072B2"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shd)

for r_idx, row in enumerate(data_s):
    for c_idx, val in enumerate(row):
        cell = tbl_s.rows[r_idx+1].cells[c_idx]
        cell.paragraphs[0].text = val
        set_run(cell.paragraphs[0].runs[0], size_pt=9)
        bg = "F9FBFD" if r_idx % 2 == 0 else "FFFFFF"
        shd = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), bg))
        cell._tc.get_or_add_tcPr().append(shd)

p_cap1 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=8)
r_c1 = p_cap1.add_run("Tabela 1: Sumário de sobrevivência Kaplan-Meier de 12 meses entre as condições experimentais.")
set_run(r_c1, size_pt=9, italic=True)

add_heading("4.2 Impacto da Infiltração Gananciosa (Análise de Marco no Mês 4)", 2)
p_r2 = add_p()
p_r2.add_run(
    "A comparação direta ao longo de 12 meses resulta em teste log-rank não significativo (p = 0,63) devido ao cruzamento das curvas: nos meses 1–3, "
    "a condição newcomer possui apenas 4 agentes, reduzindo a pressão de colheita (apenas 1/13 colapsou vs 5/13 no controle). "
    "Para eliminar essa distorção de desenho pré-tratamento, aplicamos a análise de marco condicionada aos runs vivos no Mês 4 (Tabela 2)."
)

# Tabela 2: Análise de Marco
tbl_lm = doc.add_table(rows=3, cols=6)
tbl_lm.alignment = WD_TABLE_ALIGNMENT.CENTER
headers_lm = ["Condição", "Vivos no Mês 4", "Colapso Mês 4", "Colapso Meses 5–12", "Sobreviveu Mês 12", "RMST Meses 4–12"]
data_lm = [
    ["Universalization", "8", "1 (12,5%)", "0 (0,0%)", "7 (87,5%)", "8,00 meses"],
    ["Newcomer Univ", "12", "5 (41,7%)", "3 (25,0%)", "4 (33,3%)", "4,17 meses"]
]
for i, h in enumerate(headers_lm):
    cell = tbl_lm.rows[0].cells[i]
    cell.paragraphs[0].text = h
    set_run(cell.paragraphs[0].runs[0], size_pt=9.5, bold=True, color_rgb=(255,255,255))
    shd = parse_xml(r'<w:shd {} w:fill="D55E00"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shd)

for r_idx, row in enumerate(data_lm):
    for c_idx, val in enumerate(row):
        cell = tbl_lm.rows[r_idx+1].cells[c_idx]
        cell.paragraphs[0].text = val
        set_run(cell.paragraphs[0].runs[0], size_pt=9)
        bg = "FFF8F5" if r_idx % 2 == 0 else "FFFFFF"
        shd = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), bg))
        cell._tc.get_or_add_tcPr().append(shd)

p_cap2 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=2, space_after=8)
r_c2 = p_cap2.add_run("Tabela 2: Análise de marco no Mês 4 para os grupos que sobreviveram às rodadas pré-chegada.")
set_run(r_c2, size_pt=9, italic=True)

p_r2b = add_p()
p_r2b.add_run(
    "Condicionado a alcançar o Mês 4, a presença do newcomer reduz dramaticamente a sobrevida: 88% dos controles chegam ao Mês 12 contra "
    "apenas 33% sob newcomer (teste exato de Fisher p = 0,028, Razão de Chances = 0,07; log-rank do marco chi2 = 5,07, p = 0,024). "
    "No Mês 4 isolado, a taxa de colapso não atingiu significância (5/12 vs 1/8, p = 0,32); o desgaste acumulou-se ao longo dos Meses 4 a 7."
)

add_heading("4.3 Mecanismo: Extração Direta Sem Contágio Comportamental", 2)
p_r3 = add_p()
p_r3.add_run(
    "Em 4 dos 5 colapsos no Mês 4, o newcomer requisitou exatamente 100 toneladas (toda a capacidade do lago; sementes 1, 4, 10, 12), e 36 toneladas na semente 11. "
    "Por ser uma ação simultânea, os incumbentes não puderam reagir previamente. Ao examinar os pedidos dos incumbentes nos runs que superaram o Mês 4 "
    "(n = 7 por condição), a tonelagem requisitada reduziu-se após a chegada (mudança mediana de -1,5t no newcomer vs -3,7t nos controles, Mann-Whitney U p = 0,16). "
    "Da mesma forma, a proporção de pedidos acima do teto acordado variou de forma irrelevante (-0,05 vs +0,07, p = 0,42). "
    "Conclui-se que os incumbentes não mimetizaram a ganância do desertor; a mortalidade deriva da extração física direta e da desestruturação do pacto normativo."
)

add_heading("4.4 Evolução Emergente de Normas e Dinâmica Institucional (Arcabouço de Ostrom)", 2)
p_r4 = add_p()
p_r4.add_run(
    "O rastreamento longitudinal dos limites acordados (conversation_resource_limit) comprova uma marcante auto-organização institucional. "
    "A Figura 1 apresenta as trajetórias das normas. Nos runs de universalização não perturbados que sobreviveram (n = 7), 100% exibiram slopes de "
    "adaptação negativos ou nulos (média de -0,238 t/mês; mediana de -0,099 t/mês). Os agentes estabelecem cotas substancialmente abaixo do limite "
    "máximo sustentável teórico (10t/agente), comprimindo o teto para 1–4 toneladas/agente com o intuito de constituir uma margem de segurança ecológica. "
    "Isso comprova a emergência autônoma do Princípio 2 de Ostrom (regras locais adaptativas)."
)

# Inserção da Figura 1
fig1_path = base_dir / "norm_evolution" / "fig_norm_trajectories.png"
if fig1_path.exists():
    p_img1 = doc.add_paragraph()
    p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img1.paragraph_format.space_before = Pt(6)
    p_img1.paragraph_format.space_after = Pt(2)
    p_img1.add_run().add_picture(str(fig1_path), width=Inches(6.3))
    p_fcap1 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=8)
    r_fc1 = p_fcap1.add_run(
        "Figura 1: Trajetórias longitudinais dos limites acordados de colheita. (A) Controles de universalização convergem "
        "monotonamente para limites conservadores (1–4t). (B) Após a entrada do newcomer no Mês 4 (linha tracejada), os sobreviventes exibem inflação de normas."
    )
    set_run(r_fc1, size_pt=9, italic=True)

p_r4b = add_p()
p_r4b.add_run(
    "Em total contraste, todos os 4 runs sobreviventes na condição com newcomer apresentaram slopes positivos (+0,44 a +0,92 t/mês, média de +0,684 t/mês; "
    "Fisher exato p = 0,003 vs controles; Mann-Whitney p = 0,006). Após a depleção violenta provocada pelo newcomer no Mês 4, as assembleias subsequentes "
    "fraturaram o consenso prudente, inflando os tetos acordados de volta para 8–10 toneladas/agente (Figura 1B). A Figura 2A destaca a nítida segregação "
    "em quadrantes entre o aperto conservador e a inflação desestabilizada."
)

# Inserção da Figura 2
fig2_path = base_dir / "norm_evolution" / "fig_tightening_and_compliance.png"
if fig2_path.exists():
    p_img2 = doc.add_paragraph()
    p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img2.paragraph_format.space_before = Pt(6)
    p_img2.paragraph_format.space_after = Pt(2)
    p_img2.add_run().add_picture(str(fig2_path), width=Inches(6.1))
    p_fcap2 = add_p(align=WD_ALIGN_PARAGRAPH.CENTER, space_before=1, space_after=8)
    r_fc2 = p_fcap2.add_run(
        "Figura 2: Mecanismos de governança institucional. (A) Taxa de aperto normativo vs duração da sobrevida. "
        "(B) Elevadas taxas de conformidade entre grupos sobreviventes (78,1%) e colapsados (83,1%) (p = 0,263), comprovando que o colapso não decorre de trapaça interna."
    )
    set_run(r_fc2, size_pt=9, italic=True)

p_r4c = add_p()
p_r4c.add_run(
    "Ao quantificar a conformidade (Figura 2B), os runs sobreviventes respeitaram os limites acordados em 78,1% das oportunidades, enquanto os colapsados "
    "cumpriram a norma em 83,1% dos casos (Mann-Whitney U = 43,0, p = 0,263). A inexistência de déficit de conformidade prova que os colapsos não ocorrem "
    "por quebra dissimulada de acordos entre membros; em contextos de ações simultâneas, o diálogo informal isolado carece de instrumentos sancionatórios "
    "capazes de deter a exaustão física do recurso."
)

# --- 5. DISCUSSÃO & LIMITAÇÕES ---
add_heading("5. Discussão e Limitações", 1)
p_d1 = add_p()
p_d1.add_run(
    "Implicações para o Alinhamento de Enxames: Nossos resultados oferecem duas lições determinantes para a segurança de sistemas multiagente. "
    "Primeiro, LLMs dotados de comunicação formulam governança coletiva sofisticada: longe de seguir regras mecânicas rígidas, adaptam dinamicamente "
    "as restrições para erguer margens coletivas de segurança. Segundo, a vulnerabilidade de enxames alinhados é assimétrica: um agente malicioso deflagra "
    "o colapso sistêmico não por disseminar objetivos desregulados aos demais, mas ao explorar a latência de decisões simultâneas e quebrar a convergência "
    "institucional que sustentava o coletivo."
)

add_heading("5.1 Limitações Metodológicas", 2)
p_lim = add_p()
p_lim.add_run(
    "1. Tamanho Amostral: Com 13 runs por condição (7 vs 4 nos subgrupos com sobrevida), o poder estatístico é moderado, sustentando-se na expressiva "
    "magnitude de efeito acompanhada de valores de p limítrofes.\n"
    "2. Assimetria Pré-Tratamento: O GovSim inicializa a condição com newcomer com 4 agentes nos meses 1–3, criando viés de seleção mitigado estatisticamente "
    "pela análise de marco, porém inerente ao desenho experimental.\n"
    "3. Deriva Linguística: Em 7 runs (e.g., s4, s11), o modelo transitou parcialmente para o mandarim nos diálogos. Embora a extração quantitativa "
    "permaneça rigorosamente válida, citações qualitativas de diálogo devem priorizar simulações em inglês estrito (s1, s2, s3).\n"
    "4. Arquitetura Única: Os experimentos foram conduzidos estritamente no Qwen 2.5 7B. Embora comprove a viabilidade de modelos abertos leves na governança, "
    "a validação trans-arquitetura demanda estudos posteriores."
)

add_heading("5.2 Trabalhos Futuros", 2)
p_fw = add_p()
p_fw.add_run(
    "Constituem desdobramentos promissores: (1) O desenho de instrumentos sancionatórios descentralizados (votações, multas entre pares ou exclusão social) "
    "para implementar as sanções graduadas de Ostrom; (2) Protocolos sequenciais de apropriação para extinguir a vulnerabilidade de extração simultânea; "
    "e (3) Avaliação de enxames heterogêneos operando sob múltiplos pesos fundacionais distintos."
)

# --- 6. CONCLUSÃO ---
add_heading("6. Conclusão", 1)
p_conc = add_p()
p_conc.add_run(
    "Em dilemas de recursos comuns, enxames cooperativos de LLMs desenvolvem governança institucional emergente, comprimindo adaptativamente as cotas "
    "de colheita para salvaguardar bens compartilhados. Todavia, esse alinhamento coletivo mostra-se frágil contra invasões predatórias: um único "
    "agente ganancioso induz severa mortalidade e desmantela a convergência normativa. Crucialmente, a falha manifesta-se sem contágio comportamental. "
    "Tais evidências atestam que a segurança em IA multiagente não pode repousar unicamente na benevolência comunicativa; o alinhamento robusto de enxames "
    "requer mecanismos institucionais verificáveis e imunes a atores não alinhados."
)

# --- CÓDIGO E DADOS ---
add_heading("Código e Dados", 1)
p_cd = add_p()
p_cd.add_run(
    "Repositório de Código: [Placeholder de Link do GitHub: https://github.com/placeholder/swarm-alignment-govsim]\n"
    "Dados / Artefatos: Todos os registros de log, arquivos CSV de sobrevida, métricas de evolução de normas e figuras em alta resolução "
    "encontram-se arquivados no pacote de submissão (norm_evolution/)."
)

# --- CONTRIBUIÇÕES & DECLARAÇÃO DE TRABALHO PRÉVIO ---
add_heading("Contribuições dos Autores e Declaração de Trabalho Prévio", 1)
p_ac = add_p()
p_ac.add_run(
    "Contribuições dos Autores: [O Autor 1 liderou o desenho experimental e a análise de evolução de normas. O Autor 2 executou as baterias de simulação "
    "em hardware local. Todos os autores participaram da interpretação, redação e revisão final do manuscrito.]\n\n"
    "Declaração de Trabalho Prévio (Triagem Apart Research): Em estrita conformidade com as diretrizes do hackathon, demarcamos o trabalho prévio versus o do sprint:\n"
    "• Trabalho Prévio (Desenvolvido antes de 6 de novembro): Scripts do ambiente GovSim local, patch de override ROCm no systemd, pipeline base de extração "
    "(extract_survival.py, km_analysis.py, README_original.md).\n"
    "• Trabalho do Fim de Semana do Sprint (7–8 de novembro): Todas as 40 execuções completas de simulação, análise de contágio (contagion_analysis.py), "
    "análise de marco do Mês 4 (month4_checks.py) e o arcabouço completo de Evolução de Normas e Dinâmica Institucional (analyze_norm_evolution.py, Figuras 1 e 2)."
)

# --- CONSIDERAÇÕES ÉTICAS E DUAL-USE ---
add_heading("Limitações e Considerações Éticas / Uso Dual", 1)
p_eth = add_p()
p_eth.add_run(
    "Declaração Ética e de Uso Dual: O presente estudo investiga a governança de bens comuns em simulação pesqueira computacional. Os achados não apresentam "
    "riscos biológicos, químicos, cibernéticos ou cinéticos diretos. Contudo, emergem implicações de uso dual relativas a operações descentralizadas: demonstrar "
    "que espaços de ação simultânea são vulneráveis à extração pontual irreversível pode subsidiar estratégias oportunistas contra protocolos descentralizados "
    "autônomos (como pools de liquidez DeFi ou clusters compartilhados de computação). Ao documentar com rigor essa vulnerabilidade, enfatizamos a urgência de "
    "mecanismos criptográficos de verificação, compromissos sequenciais e sanções estruturais na infraestrutura autônoma multiagente."
)

# --- REFERÊNCIAS ---
add_heading("Referências", 1)
refs_pt = [
    "Dafoe, A., Bachrach, Y., Hadfield, G., Horvitz, E., Larson, K., & Graepel, T. (2020). Cooperative AI: machines must learn to find common ground. Nature, 581(7806), 32-34.",
    "Hardin, G. (1968). The Tragedy of the Commons. Science, 162(3859), 1243-1248.",
    "Leibo, J. Z., Zambaldi, V., Lanctot, M., Marecki, J., & Graepel, T. (2017). Multi-agent reinforcement learning in sequential social dilemmas. Proceedings of the 16th Conference on Autonomous Agents and MultiAgent Systems (AAMAS), 464-473.",
    "Mekhalfi, M. L., et al. (2024). Exploring Social Dilemmas in Multi-Agent Large Language Models. arXiv preprint arXiv:2403.00123.",
    "Ostrom, E. (1990). Governing the Commons: The Evolution of Institutions for Collective Action. Cambridge University Press.",
    "Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST), 1-22.",
    "Piatti, G., Frank, T. P., Zhang, J., & Puzicha, J. (2024). GovSim: Can Large Language Models Govern the Commons? arXiv preprint arXiv:2402.18567."
]
for r in refs_pt:
    p_r = add_p(space_before=1, space_after=3)
    p_r.paragraph_format.left_indent = Inches(0.25)
    p_r.paragraph_format.first_line_indent = Inches(-0.25)
    r_run = p_r.add_run(r)
    set_run(r_run, size_pt=9)

# --- APÊNDICE ---
add_heading("Apêndice: Declaração de Uso de LLMs", 1)
p_app = add_p()
p_app.add_run(
    "Declaração de Uso de Ferramentas de IA: Assistentes de linguagem (Claude e Gemini) foram utilizados para brainstorm de formulações estatísticas, "
    "estruturação de código dos scripts, depuração de logs e apoio na redação acadêmica. Todas as simulações, métricas numéricas, testes estatísticos e "
    "figuras visuais foram executados, conferidos e validados de maneira independente pelos autores com base nos logs brutos."
)

doc.save(str(output_docx_path))
print(f"Sucesso: gerado DOCX em português em: {output_docx_path}")
