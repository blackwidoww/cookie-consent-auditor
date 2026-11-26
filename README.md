> [!WARNING]
> **Ferramenta de testes e estudo.** Este projeto foi feito para aprendizado em cibersegurança e privacidade. Os resultados são um apoio técnico, não uma análise jurídica de conformidade. Use em sites seus, de teste ou públicos.

# Cookie Consent Auditor

Ferramenta em Python que verifica **quais cookies um site grava no navegador antes de qualquer interação com o banner de consentimento**, e sinaliza os que não são essenciais (analytics, publicidade, redes sociais).
Gravar esse tipo de cookie antes do consentimento é um problema de conformidade com a **LGPD** e o **GDPR**.

Projeto de estudo em cibersegurança e privacidade, feito para rodar localmente.

## Como funciona

1. Abre a página num navegador **headless** (Chromium via Playwright), num contexto limpo, sem cookies prévios.
2. **Não clica em nada:** Espera a página carregar e depois captura todos os cookies gravados até ali (incluindo os de terceiros).
3. Classifica cada cookie contra uma base de assinaturas (`trackers.json`), por nome e, para cookies de terceiros, por domínio.
4. Gera um relatório com o status de cada cookie:
   - **Violação**: não essencial gravado antes do consentimento
   - **Revisar**: cookie desconhecido, precisa de análise manual
   - **OK**: cookie essencial (sessão, CSRF, segurança, gestão de consentimento)

## Instalação

Requer Python 3.10+.

```bash
pip install -r requirements.txt
playwright install chromium
```

No Windows, se o comando `playwright` não for reconhecido:

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Uso

### Linha de comando

```bash
python main.py http://localhost:8000
python main.py http://localhost:8000 --wait 8 --out relatorios
```

Gera `out/report.html`, `out/report.css` e `out/report.json`. Para visualizar, abra o `report.html` no navegador.

### Interface web local (barra de pesquisa)

```bash
python app.py
```

Abra `http://127.0.0.1:5000`, digite o endereço do site e clique em **Auditar**.

> O servidor escuta apenas em `127.0.0.1`. Não altere para `0.0.0.0`: isso permitiria que outras pessoas da rede usassem a sua máquina para visitar sites.

### Página de teste

A pasta `test_site/` tem uma página que grava cookies não essenciais (`_ga`, `_gid`, `_fbp`, `_gcl_au`) antes de qualquer clique, mais um cookie essencial e um desconhecido.

```bash
cd test_site
python -m http.server 8000
```

Em outro terminal, na pasta principal:

```bash
python main.py http://localhost:8000          # esperado: 4 violações, 1 revisar, 1 ok
python main.py "http://localhost:8000/?clean=1"   # controle: só o cookie essencial
```

## Estrutura

```
cookie-auditor/
├── main.py          # linha de comando
├── app.py           # interface web local (Flask)
├── auditor.py       # captura dos cookies (Playwright)
├── classifier.py    # classificação contra a base de trackers
├── report.py        # relatório em JSON e HTML
├── report.css       # visual do relatório
├── trackers.json    # base de assinaturas de trackers
├── requirements.txt
└── test_site/
    └── index.html   # página de teste com cookies plantados
```

## Limitações

- A base `trackers.json` é pequena e serve de exemplo. Ela pode ser ampliada com fontes como a Open Cookie Database.
- A classificação é feita por nome e domínio do cookie. Não analisa `localStorage`, fingerprinting nem pixels de rastreamento.
- Alguns sites bloqueiam navegadores automatizados, e nesse caso o resultado pode vir incompleto.
- O relatório é um apoio técnico, **não uma análise jurídica** de conformidade.

## Uso responsável

**ATENÇÃO:** Use a ferramenta em sites seus, em páginas de teste ou em sites públicos, **uma página por vez** e sem automatizar em massa. Não divulgue conclusões do tipo "o site X viola a lei" com base apenas em um teste isolado.

## Ideias para evoluir

- Detectar o banner de consentimento e comparar os cookies **antes e depois** de aceitar
- Importar a Open Cookie Database para ampliar a base de assinaturas
- Exportação em CSV
- Relatórios com data e hora no nome do arquivo
