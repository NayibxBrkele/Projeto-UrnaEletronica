# Limitações e Pontos de Atenção da Reconstrução

Este documento registra as limitações técnicas e teóricas observadas na base documental do projeto. Os arquivos presentes no diretório `codigo-fonte/` foram preservados no seu formato de reconstrução; estas notas servem para garantir que os comentários internos do código não sejam confundidos com comprovação histórica oficial.

## 1. Estruturas descritas como "exatas"
O arquivo `include/ue2000_types.h` utiliza expressões como "estruturas binárias exatas" para descrever mapas de EEPROM, portas de I/O, modos operacionais e um formato `.SIG`. No entanto, o repositório não contém documentação primária suficiente para validar essas especificações como o layout definitivo da UE2000. Tais estruturas devem ser interpretadas como modelos teóricos de reconstrução, até que fontes documentais independentes confirmem cada campo, *offset* e valor.

## 2. `ckpack.c` e a rotina `ASSINA`
O arquivo `src/virtuos/ckpack.c` contém um cálculo MD5 e uma função `assina_256_compute` que gera 32 bytes por meio de transformações aritméticas simples. A presença desta função é estritamente didática. Ela não representa a recuperação do algoritmo oficial (ASSINA) utilizado na época, tampouco constitui uma assinatura criptográfica real e segura para fins modernos.

## 3. Implementações Criptográficas Proprietárias (CEPESC/ABIN)
O módulo `src/aplic/cepesc_crypto.c` contém uma rotina de rede de Feistel demonstrativa com constantes fixas. Conforme documentado internamente no código `src/aplic/vvota.c`, a rotina criptográfica atua exclusivamente como um *placeholder* (simulador) para a arquitetura de software, não refletindo a implementação proprietária original fornecida pelo CEPESC/ABIN.

## 4. Comentários de cabeçalho e documentação interna
Comentários presentes nos códigos-fonte (como "TSE-UE2000" ou "layout exato") refletem a intenção arquitetônica da reconstrução em simular o ambiente da época. Eles possuem caráter de estudo e não substituem referências primárias ou artefatos de hardware com cadeia de custódia.

## 5. Processo de Build e Compilação
- A compilação nativa (com GCC, por exemplo) requer a criação prévia dos diretórios de saída `FI_C/virtuos/`, `FI_C/aplic/` e `RAM_E/`. O script `build-host.sh` foi incluído no projeto para automatizar essa preparação do ambiente.
- Os artefatos gerados pela compilação moderna com sufixos `.exe` e `.com` são executáveis nativos do sistema hospedeiro atual. Eles simulam a execução, mas não são binários originais compilados para arquiteturas MS-DOS de 16 bits.

## 6. Interface Textual (C) versus Interface Gráfica (Python)
O arquivo `src/aplic/ui_urna.c` implementa uma interface textual demonstrativa em C. Esta implementação não deve ser confundida com a aplicação gráfica contida em `interface-teorica/` (Python/Tkinter), nem serve como prova definitiva de que a disposição histórica da tela da UE2000 fosse idêntica à apresentada na saída do terminal.
