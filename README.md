# 🔧 Repositório de TI - Documentação e Registro de Erros

Um sistema desktop de gerenciamento de incidentes e base de conhecimento (playbooks) projetado para equipes de Suporte de TI (Nível 1 e 2). O software centraliza soluções de problemas de forma estruturada, permitindo o anexo de evidências visuais e buscas rápidas por palavras-chave, otimizando o tempo de resposta (SLA).

## 🚀 Funcionalidades Principais

- **CRUD Completo de Procedimentos:** Cadastro, consulta, edição e exclusão de erros e soluções.
- **Banco de Dados Relacional:** Persistência local utilizando SQLite3 com integridade referencial (`FOREIGN KEY`) e deleção em cascata.
- **Gerenciamento de Mídia:** Armazenamento automático e renomeação segura de capturas de tela/prints de erros anexados.
- **Filtros Dinâmicos em Tempo Real:** Mecanismo de busca instantânea por título do erro ou por palavras contidas dentro da solução.
- **Interface Responsiva & Temas:** Interface gráfica moderna desenvolvida em Tkinter com suporte completo a **Modo Claro** e **Modo Escuro (Dark Mode)**.

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Interface Gráfica:** Tkinter / ttk
- **Banco de Dados:** SQLite3
- **Tratamento de Imagens:** Pillow (PIL)

---

## 📦 Como Compilar e Gerar o Executável (.exe)

Para distribuir o sistema para a equipe de suporte rodar sem precisar instalar o Python na máquina, você pode gerar um executável utilizando o **PyInstaller**.

1. Instale as dependências necessárias no seu terminal:
   ```bash
   pip install Pillow pyinstaller
