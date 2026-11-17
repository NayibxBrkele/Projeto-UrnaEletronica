# Fontes e Referências Documentais

Este documento centraliza as fontes, laudos técnicos, fragmentos de código e artigos utilizados para a pesquisa OSINT (Open Source Intelligence) e reconstrução da base de software da Urna Eletrônica UE2000.

## Inventário de Fontes e Referências

| Identificador | Fonte / Artefato | Descrição e Contexto na Reconstrução |
|:---:|---|---|
| **REF-001** | **Artefatos de Lote VirtuOS (`.bat`)** | Conjunto de ficheiros originais de orquestração (`SETUP.BAT`, `instala.bat`, `roda_*.bat`) recuperados via investigação histórica em fóruns e diretórios web antigos. Base fundamental para mapear o fluxo de execução, variáveis de ambiente e chamadas do sistema Microbase VirtuOS. |
| **REF-002** | **Relatórios Técnicos (Unicamp e TPS)** | Documentação técnica e relatórios de segurança (incluindo referências a testes públicos posteriores), usados nesta pesquisa para compreender a evolução e a arquitetura das funções de verificação de integridade (`ckpack`), uso de algoritmos de *hash* (MD5) e chamadas ao perímetro criptográfico (`ASSINA`). |
| **REF-003** | **Laudo Pericial - Processo 405/2000 (Santo Estêvão/BA)** | Estudo de caso e laudo pericial histórico, documentado na literatura de auditoria independente. A referência serviu para mapear a dificuldade histórica de validação dos binários devido à indisponibilidade de mídias físicas originais (CD-ROMs/Disquetes) durante as auditorias da época. |
| **REF-004** | **Publicações do Fórum "Voto Seguro" e Academia** | Artigos, laudos e descrições técnicas publicadas no final da década de 1990 e início dos anos 2000 por investigadores como o Eng. Amilcar Brunazo Filho e o Prof. Pedro Rezende (UnB). Forneceram a base teórica sobre o comportamento do MS-DOS na urna, limites de hardware e a estrutura de diretórios (`RAM_E/`, `FI_C/`). |

## Notas sobre a Cadeia de Custódia e OSINT

A natureza deste projeto é estritamente **histórica, acadêmica e baseada em evidências públicas**. 

Os ficheiros e fragmentos referenciados não possuem cadeia de custódia oficial certificada pelas autoridades eleitorais. Eles foram agregados através de um extenso trabalho de engenharia reversa documental, garimpando cópias de segurança em arquivos da internet (Web Archive), repositórios HTTP legados e documentações técnicas distribuídas pela comunidade brasileira de segurança da informação ao longo das últimas duas décadas.
