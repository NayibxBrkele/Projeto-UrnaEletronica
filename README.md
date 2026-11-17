# UE2000 — Reconstrução Documental e Arquitetura de Software

Projeto independente de pesquisa histórica, investigação (OSINT) e engenharia reversa sobre o ambiente de software associado à urna eletrônica brasileira **UE2000**. 

O repositório separa deliberadamente a **base documental histórica em C e MS-DOS** da **interface gráfica moderna de demonstração em Python**.

> ⚠️ **Aviso de autenticidade:** Este projeto não contém o código-fonte original integral, não é uma imagem forense, não é um firmware oficial e não demonstra que os ficheiros aqui reunidos sejam cópias exatas das urnas em eleição. Trata-se de uma reconstrução arquitetural orientada por manuais públicos, laudos técnicos e arquivos antigos garimpados via OSINT. As lacunas e hipóteses estão explicitamente documentadas.

## Organização do Repositório

    Projeto-UrnaEletronica/
    ├── README.md
    ├── .gitignore
    ├── CONTRIBUTING.md
    ├── AVISO-LICENCA.txt
    ├── codigo-fonte/
    │   ├── include/
    │   ├── src/
    │   │   ├── virtuos/
    │   │   └── aplic/
    │   ├── arquivos_lote/
    │   ├── Makefile
    │   ├── build-host.sh
    │   └── LEIA-ME_BASE_DOCUMENTAL.md
    ├── interface-teorica/
    │   ├── urna_gui.py
    │   ├── candidatos_2026_sp.json
    │   ├── iniciar_interface.sh
    │   └── LEIA-ME-GUI.txt
    └── docs/
        ├── METODOLOGIA-E-LIMITACOES.md
        ├── PONTOS-DE-ATENCAO-DO-CODIGO.md
        ├── INVENTARIO-DA-BASE.md
        └── FONTES-E-REFERENCIAS.md

### `codigo-fonte/` — Base Documental Reconstruída
Contém os ficheiros da arquitetura base: cabeçalhos C, módulos de simulação do sistema Microbase VirtuOS (`src/virtuos/`), rotinas de aplicação (`src/aplic/`) e ficheiros de lote MS-DOS (`arquivos_lote/`). Foi acrescentado apenas o `build-host.sh` para auxiliar na preparação de diretórios de compilação.

*A presença de estruturas ou rotinas criptográficas nesta pasta não comprova o seu uso histórico exato. Consulte os arquivos em `docs/` para entender as limitações metodológicas.*

### `interface-teorica/` — Demonstração Moderna
Contém a recriação da interface de votação desenvolvida em **Python 3 (Tkinter)**. Esta é uma ferramenta visual contemporânea, construída exclusivamente para interagir com a base reconstruída em C. A linguagem Python não fazia parte do ecossistema da UE2000.

## Compilação da base C (Ambiente Hospedeiro)

O repositório inclui regras para compilar os executáveis de demonstração nativamente com GCC. Em ambientes Linux/Unix com `gcc` e `make` instalados:

    cd codigo-fonte
    ./build-host.sh

O script auxiliar cria os diretórios em RAM simulada esperados pelo sistema e executa o `make`. Os ficheiros gerados terminam em `.exe` ou `.com`, porém **são binários nativos do seu sistema hospedeiro**, servindo apenas para demonstração do fluxo lógico, e não executáveis compatíveis com hardware de 16-bits da época.

## Limites Técnicos Conhecidos

- Não há binários oficiais, chaves criptográficas (como as do CEPESC/ABIN) ou manifestos originais completos.
- O ficheiro `SETUP.BAT` funciona como um orquestrador de ambiente, não devendo ser classificado como "firmware".
- As verificações de integridade simuladas no código (ex: MD5 e rotinas `ASSINA`) são ilustrativas da arquitetura proposta nos laudos, não refletindo a segurança original do equipamento.

## Licença
Este material não possui licença de código aberto para modificação ou redistribuição comercial/oficial. Para mais detalhes sobre os limites de direitos autorais e o uso acadêmico (Fair Use), consulte o ficheiro `AVISO-LICENCA.txt`.
