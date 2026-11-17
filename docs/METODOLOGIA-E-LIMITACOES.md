# Metodologia e Limites da Reconstrução

## Objetivo
Documentar uma reconstrução técnica do ambiente de software associado à UE2000, baseada puramente em evidências públicas (OSINT), manuais, laudos históricos e análise de fluxo. 

O objetivo deste repositório não é afirmar que os arquivos refletem integralmente o software instalado nas urnas usadas nas eleições. O pacote atual é uma **reconstrução de trabalho e estudo de arquitetura**, e não uma imagem forense autenticada.

## Diretrizes da Pesquisa
Durante a análise e o desenvolvimento, o projeto buscou:
- Distinguir claramente o que é o comportamento observável nos arquivos de lote da época do que é inferência estrutural moderna.
- Isolar a arquitetura da **UE2000** de gerações posteriores, especialmente para não confundir o sistema VirtuOS (baseado em DOS) com os sistemas Uenux (Linux) adotados a partir de 2008.

## Limitações Materiais
O material atualmente presente no diretório `codigo-fonte/` reflete a fronteira do que é possível recuperar publicamente. O repositório **não** inclui:
- Binários históricos originais ou autenticados pelas autoridades;
- Imagens integrais preservadas de mídias originais (disquetes, discos ou CD-ROMs);
- Código-fonte oficial comprovadamente extraído do equipamento;
- Executáveis, chaves e bibliotecas proprietárias (como os algoritmos reais do CEPESC/ABIN);
- Cadeia de custódia que vincule os arquivos deste repositório a uma urna específica.
