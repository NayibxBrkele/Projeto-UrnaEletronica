# Base documental UE2000 — sem interface gráfica

Esta pasta é a camada de reconstrução documental/técnica em linguagem C e
arquivos de lote DOS. Não contém interface gráfica moderna e não contém Python.

## Cuidado com a autenticidade

Esta base NÃO é uma cópia forense do software oficial instalado nas urnas.
Ela reúne módulos e estruturas de reconstrução usados no projeto, com graus
diferentes de sustentação documental. O fato de um arquivo estar presente aqui
não prova que ele existiu com esse conteúdo na UE2000 original.

A base deve ser lida como reconstrução técnica orientada pelas evidências:
- C e arquivos de lote são tecnologias compatíveis com a época;
- nomes/fluxos documentados e inferidos precisam continuar identificados como
  tais, sem converter inferência em fato;
- executáveis, dependências, manifestos, documentação e cadeia de custódia
  ausentes não foram preenchidos por suposição;
- SETUP.BAT não deve ser chamado de firmware;
- não há implementação ou alegação de criptografia oficial, chave oficial,
  assinatura oficial ou comportamento de hardware não demonstrado pelas fontes.

## Organização

- `include/`: cabeçalhos C da reconstrução.
- `src/virtuos/`: módulos de camada DOS/VirtuOS reconstruídos.
- `src/aplic/`: módulos de aplicação/votação reconstruídos.
- `arquivos_lote/`: SETUP.BAT, instala.bat e variantes roda_*.bat da árvore
  de trabalho. A presença não comprova instalação/execução em pleito real.
- `Makefile`: regras de compilação do ambiente demonstrativo.

## O que deliberadamente não está aqui

- interface gráfica Tkinter ou qualquer interface moderna;
- Python, pois não fazia parte da plataforma histórica da UE2000;
- binários oficiais, firmware oficial, dumps de mídia autenticados ou chaves;
- dados eleitorais reais de 2026.

A interface atual e o conjunto de candidatos reais de 2026 ficam no pacote
`UE2000_Interface_Grafica_Eleicoes2026_SP.zip`, separados desta base.
