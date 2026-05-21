# 🔍 Detector de Sujeira, Riscos e Resíduos em Imagens

Ferramenta em Python para **inspeção visual automatizada** de superfícies. Compara uma imagem de referência limpa com uma imagem analisada e identifica automaticamente sujeira, riscos e resíduos, contornando cada defeito encontrado.

![Exemplo de resultado](resultado_deteccao.png)

---

## ✨ Funcionalidades

- Detecta **sujeira**, **riscos finos** e **resíduos** sem depender de comparação direta de brilho
- Funciona mesmo com diferenças de **iluminação** entre as imagens
- Identifica e exclui automaticamente a **borda do disco/ROI circular** para evitar falsos positivos
- Gera um **painel diagnóstico 2×2** com referência, imagem analisada, máscara de defeitos e resultado anotado
- Produz um **relatório no terminal** com posição, tamanho e área de cada defeito
- Todos os parâmetros de sensibilidade são **facilmente ajustáveis**

---

## 🖼️ Como funciona

O script combina duas técnicas de visão computacional para robustez em diferentes condições de iluminação:

```
Imagem suja
    │
    ├─► Threshold Adaptativo Gaussiano ──► detecta sujeira e resíduos
    │                                      (regiões escuras relativas ao entorno)
    │
    ├─► Detector de Bordas Canny ─────► detecta riscos
    │                                      (transições bruscas de intensidade)
    │
    └─► Combina máscaras → Morfologia → Contornos → Resultado anotado
```

**Fluxo passo a passo:**

1. Carrega e alinha as duas imagens (redimensiona se necessário)
2. Detecta o disco/ROI circular na referência via `HoughCircles`
3. Cria zona de exclusão na borda do disco (evita falso positivo na borda)
4. Aplica **threshold adaptativo** para encontrar sujeira e resíduos
5. Aplica **Canny** para encontrar riscos e arranhões
6. Une as duas máscaras e aplica operações morfológicas para limpar ruído
7. Contorna cada defeito com **bounding box** (vermelho) e **contorno exato** (ciano)
8. Salva o painel diagnóstico e exibe o relatório

---

## 📋 Requisitos

- Python 3.8+
- OpenCV
- NumPy

---

## ⚙️ Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/detector-sujeira.git
cd detector-sujeira

# Instale as dependências
pip install opencv-python numpy
```

> **Dica:** use um ambiente virtual para não poluir o Python global.
>
> ```bash
> python -m venv .venv
> source .venv/bin/activate   # Linux/macOS
> .venv\Scripts\activate      # Windows
> pip install opencv-python numpy
> ```

---

## 🚀 Uso

### Linha de comando

```bash
# Usando nomes padrão (limpo.png e sujo.png na mesma pasta)
python detectar_sujeira.py

# Especificando os arquivos
python detectar_sujeira.py referencia.png amostra.png

# Especificando também o arquivo de saída
python detectar_sujeira.py referencia.png amostra.png resultado.png
```

### Como módulo Python

```python
from detectar_sujeira import detectar_defeitos

defeitos, resultado, painel = detectar_defeitos(
    imagem_limpa_path="limpo.png",
    imagem_suja_path="sujo.png",
    output_path="resultado_deteccao.png",
)

print(f"Total de defeitos: {len(defeitos)}")
```

---

## 📂 Estrutura esperada de arquivos

```
detector-sujeira/
├── detectar_sujeira.py     # script principal
├── limpo.png               # imagem de referência (sem defeitos)
├── sujo.png                # imagem a ser analisada
├── resultado_deteccao.png  # gerado automaticamente
└── README.md
```

---

## 🎛️ Parâmetros de ajuste fino

Todos os parâmetros podem ser passados diretamente à função `detectar_defeitos()` ou ajustados na seção `if __name__ == "__main__"` do script:

| Parâmetro | Padrão | Efeito |
|---|---|---|
| `adaptativo_block` | `21` | Tamanho do bloco do threshold adaptativo (deve ser ímpar). **↑ maior** → menos sensível a variações suaves |
| `adaptativo_c` | `8` | Constante subtraída na binarização. **↑ maior** → ignora diferenças pequenas de intensidade |
| `canny_low` | `20` | Limiar inferior do Canny. **↓ menor** → detecta riscos mais finos |
| `canny_high` | `60` | Limiar superior do Canny. **↑ maior** → exige bordas mais fortes |
| `area_minima` | `20` | Área mínima em px² de um contorno para ser considerado defeito. **↑ maior** → ignora pontos de ruído |
| `dilatar` | `2` | Iterações de dilatação morfológica. **↑ mais** → une regiões fragmentadas próximas |
| `excluir_borda_disco` | `12` | Largura em px da borda do disco a ser ignorada. Evita falso positivo na transição disco/fundo |

### Exemplos de ajuste

```python
# Detecção mais agressiva (pega mais defeitos, pode incluir ruído)
detectar_defeitos(..., adaptativo_c=4, canny_low=10, area_minima=10)

# Detecção conservadora (só defeitos grandes e evidentes)
detectar_defeitos(..., adaptativo_c=15, canny_low=40, area_minima=100)

# Unir defeitos espalhados em grupos maiores
detectar_defeitos(..., dilatar=4)
```

---

## 📊 Saída

### Terminal

```
────────────────────────────────────────────────────────
  DETECTOR DE SUJEIRA / RISCOS / RESÍDUOS
────────────────────────────────────────────────────────
  Referência  : limpo.png
  Analisada   : sujo.png
  Resultado   : resultado_deteccao.png
────────────────────────────────────────────────────────
  ROI (disco) : centro=(192,172)  raio=106px
  Defeitos encontrados: 89

    #001  pos=( 11,310)  tam=  10×12px  área=    48px²
    #002  pos=( 192,308)  tam=  32×16px  área=   185px²
    ...
────────────────────────────────────────────────────────
```

### Imagem de resultado

O arquivo de saída é um **painel 2×2** contendo:

| Posição | Conteúdo |
|---|---|
| Superior esquerdo | Imagem de referência (limpa) com o disco delimitado em verde |
| Superior direito | Imagem analisada original |
| Inferior esquerdo | Máscara binária dos defeitos detectados |
| Inferior direito | Imagem analisada com defeitos contornados em vermelho/ciano |

---

## 🧩 Limitações conhecidas

- Requer que a **câmera/posição** seja aproximadamente a mesma entre as imagens (sem rotação ou perspectiva muito diferente)
- Para imagens sem ROI circular (disco), o script analisa a imagem inteira e pode detectar mais falsos positivos no fundo
- Variações muito grandes de iluminação (diferentes fontes de luz) podem exigir ajuste do `adaptativo_block` e `adaptativo_c`

---

## 🛠️ Tecnologias

- [OpenCV](https://opencv.org/) — processamento de imagem
- [NumPy](https://numpy.org/) — operações matriciais

---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.
