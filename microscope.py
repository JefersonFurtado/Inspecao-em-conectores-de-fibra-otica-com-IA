"""
Detector de Sujeira, Riscos e Resíduos em Imagens
===================================================
Compara uma imagem "suja" com uma imagem de referência "limpa" e contorna
as regiões com defeitos encontrados (sujeira, riscos, resíduos).

Uso:
    python detectar_sujeira.py [limpa] [suja] [saida]

Exemplos:
    python detectar_sujeira.py                           # usa limpo.png / sujo.png
    python detectar_sujeira.py ref.png amostra.png out.png

Dependências:
    pip install opencv-python numpy
"""

import cv2
import numpy as np
import sys
import os


# ──────────────────────────────────────────────────────────────────────────────
# Função principal
# ──────────────────────────────────────────────────────────────────────────────
def detectar_defeitos(
    imagem_limpa_path: str,
    imagem_suja_path: str,
    output_path: str = "resultado_deteccao.png",
    # --- parâmetros de detecção ---
    adaptativo_block: int = 21,   # tamanho do bloco do threshold adaptativo (ímpar)
    adaptativo_c: int = 8,        # constante subtraída na binarização
    canny_low: int = 20,          # limiar inferior do detector de bordas Canny
    canny_high: int = 60,         # limiar superior do detector de bordas Canny
    area_minima: int = 20,        # área mínima (px²) para considerar um contorno
    dilatar: int = 2,             # iterações de dilatação (une regiões próximas)
    excluir_borda_disco: int = 12, # largura (px) da borda do disco a ignorar
):
    """
    Detecta sujeira, riscos e resíduos em uma imagem comparando com referência limpa.

    Retorna:
        defeitos  : lista de contornos OpenCV dos defeitos encontrados
        resultado : imagem BGR anotada com as regiões marcadas
        painel    : painel 2×2 com referência / analisada / máscara / resultado
    """

    # ── 1. Carregar imagens ────────────────────────────────────────────────────
    ref = cv2.imread(imagem_limpa_path)
    alvo = cv2.imread(imagem_suja_path)

    if ref is None:
        raise FileNotFoundError(f"Imagem limpa não encontrada: {imagem_limpa_path}")
    if alvo is None:
        raise FileNotFoundError(f"Imagem suja não encontrada: {imagem_suja_path}")

    # ── 2. Garantir mesmo tamanho ──────────────────────────────────────────────
    h, w = alvo.shape[:2]
    if ref.shape[:2] != (h, w):
        ref = cv2.resize(ref, (w, h), interpolation=cv2.INTER_AREA)

    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    alvo_gray = cv2.cvtColor(alvo, cv2.COLOR_BGR2GRAY)

    # ── 3. Detectar o disco/ROI circular na imagem de referência ──────────────
    blur_ref = cv2.GaussianBlur(ref_gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blur_ref, cv2.HOUGH_GRADIENT, dp=1, minDist=50,
        param1=50, param2=25, minRadius=30, maxRadius=min(h, w) // 2
    )

    disco_encontrado = circles is not None
    if disco_encontrado:
        cx, cy, r = np.round(circles[0][0]).astype(int)
        disco_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(disco_mask, (cx, cy), r, 255, -1)
        # Anel de exclusão: borda do disco não é defeito
        borda_exclusao = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(borda_exclusao, (cx, cy), r + excluir_borda_disco, 255, excluir_borda_disco * 2)
    else:
        print("[AVISO] Disco circular não detectado — analisando imagem inteira.")
        disco_mask = None
        borda_exclusao = np.zeros((h, w), dtype=np.uint8)

    # ── 4. Threshold adaptativo (detecta regiões escuras locais = sujeira) ────
    mascara_thresh = cv2.adaptiveThreshold(
        alvo_gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=adaptativo_block,
        C=adaptativo_c,
    )

    # ── 5. Bordas Canny (detecta riscos = transições bruscas) ─────────────────
    blur_alvo = cv2.GaussianBlur(alvo_gray, (3, 3), 0)
    mascara_bordas = cv2.Canny(blur_alvo, canny_low, canny_high)

    # ── 6. Remover a borda do próprio disco das máscaras ──────────────────────
    mascara_thresh = cv2.bitwise_and(mascara_thresh, cv2.bitwise_not(borda_exclusao))
    mascara_bordas = cv2.bitwise_and(mascara_bordas, cv2.bitwise_not(borda_exclusao))

    # ── 7. Combinar as duas máscaras ──────────────────────────────────────────
    mascara_total = cv2.bitwise_or(mascara_thresh, mascara_bordas)

    # ── 8. Morfologia: remover ruído e unir regiões próximas ──────────────────
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mascara_total = cv2.morphologyEx(mascara_total, cv2.MORPH_OPEN, kernel, iterations=1)
    mascara_total = cv2.dilate(mascara_total, kernel, iterations=dilatar)

    # ── 9. Encontrar e filtrar contornos ──────────────────────────────────────
    contornos, _ = cv2.findContours(mascara_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    defeitos = [c for c in contornos if cv2.contourArea(c) >= area_minima]

    # ── 10. Desenhar resultado ────────────────────────────────────────────────
    resultado = alvo.copy()

    # Borda do disco (verde) — referência visual
    if disco_encontrado:
        cv2.circle(resultado, (cx, cy), r, (0, 220, 0), 2)

    for i, c in enumerate(defeitos):
        x, y, ww, hh = cv2.boundingRect(c)
        # Contorno exato (amarelo-ciano)
        cv2.drawContours(resultado, [c], -1, (0, 255, 255), 1)
        # Bounding box (vermelho)
        cv2.rectangle(resultado, (x, y), (x + ww, y + hh), (0, 0, 255), 1)
        # Rótulo
        label = f"#{i + 1}"
        cv2.putText(resultado, label, (x, max(y - 3, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.3, (50, 50, 255), 1, cv2.LINE_AA)

    # ── 11. Painel diagnóstico 2×2 ────────────────────────────────────────────
    mask_bgr = cv2.cvtColor(mascara_total, cv2.COLOR_GRAY2BGR)
    ref_vis = ref.copy()
    if disco_encontrado:
        cv2.circle(ref_vis, (cx, cy), r, (0, 220, 0), 2)

    top = np.hstack([ref_vis, alvo.copy()])
    bot = np.hstack([mask_bgr, resultado])

    labels_quad = [
        "REFERENCIA (limpa)",
        "IMAGEM ANALISADA",
        "MASCARA DE DEFEITOS",
        f"RESULTADO: {len(defeitos)} defeito(s)",
    ]
    quads = [top[:h, :w], top[:h, w:], bot[:h, :w], bot[:h, w:]]
    for quad, lbl in zip(quads, labels_quad):
        cv2.putText(quad, lbl, (6, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)

    painel = np.vstack([top, bot])
    cv2.imwrite(output_path, painel)

    # ── 12. Relatório no terminal ──────────────────────────────────────────────
    sep = "─" * 56
    print(f"\n{sep}")
    print(f"  DETECTOR DE SUJEIRA / RISCOS / RESÍDUOS")
    print(sep)
    print(f"  Referência  : {imagem_limpa_path}")
    print(f"  Analisada   : {imagem_suja_path}")
    print(f"  Resultado   : {output_path}")
    print(sep)
    if disco_encontrado:
        print(f"  ROI (disco) : centro=({cx},{cy})  raio={r}px")
    print(f"  Defeitos encontrados: {len(defeitos)}")
    print()
    for i, c in enumerate(defeitos):
        x, y, ww, hh = cv2.boundingRect(c)
        area = cv2.contourArea(c)
        print(f"    #{i+1:03d}  pos=({x:4d},{y:4d})  tam={ww:4d}×{hh:3d}px  área={area:6.0f}px²")
    print(f"{sep}\n")

    return defeitos, resultado, painel


# ──────────────────────────────────────────────────────────────────────────────
# Execução via linha de comando
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    LIMPA  = sys.argv[1] if len(sys.argv) > 1 else "limpo.png"
    SUJA   = sys.argv[2] if len(sys.argv) > 2 else "sujo.png"
    SAIDA  = sys.argv[3] if len(sys.argv) > 3 else "resultado_deteccao.png"

    defeitos, resultado_img, painel_img = detectar_defeitos(
        imagem_limpa_path=LIMPA,
        imagem_suja_path=SUJA,
        output_path=SAIDA,
        # ─── Ajuste fino ───────────────────────────────────────────────────
        adaptativo_block=21,   # ↑ bloco maior → menos sensível a gradientes suaves
        adaptativo_c=8,        # ↑ C maior → menos sensível (ignora diferenças pequenas)
        canny_low=20,          # ↓ limiar menor → detecta mais riscos finos
        canny_high=60,
        area_minima=20,        # ↑ área maior → ignora pontos de ruído
        dilatar=2,             # ↑ mais iterações → une regiões fragmentadas
        excluir_borda_disco=12,
        # ───────────────────────────────────────────────────────────────────
    )

    # Exibição interativa (opcional — requer display)
    try:
        cv2.imshow("Deteccao de Defeitos — pressione qualquer tecla para fechar", painel_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception:
        pass  # ambiente sem display (servidor/CI) — apenas arquivo salvo