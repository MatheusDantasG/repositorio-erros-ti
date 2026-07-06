import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

# Cria a pasta de imagens se ela não existir
if not os.path.exists("imagens_suporte"):
    os.makedirs("imagens_suporte")

# Variáveis globais de controle
lista_fotos_novas = []           
fotos_para_excluir_do_disco = []  
id_procedimento_em_edicao = None
modo_noturno_ativo = False       


# --- BANCO DE DATOS ---
def conectar_bd():
    conn = sqlite3.connect("repositorio_suporte.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS procedimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            conteudo TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos_procedimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            procedimento_id INTEGER NOT NULL,
            caminho_foto TEXT NOT NULL,
            FOREIGN KEY (procedimento_id) REFERENCES procedimentos(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    return conn, cursor


# --- FUNÇÕES DO SISTEMA ---
def selecionar_fotos():
    global lista_fotos_novas
    arquivos = filedialog.askopenfilenames(
        title="Selecionar Imagens do Erro",
        filetypes=[("Arquivos de Imagem", "*.jpg *.jpeg *.png *.bmp")],
    )
    if arquivos:
        for arquivo in arquivos:
            if arquivo not in lista_fotos_novas:
                lista_fotos_novas.append(arquivo)
        atualizar_label_fotos()


def atualizar_label_fotos():
    global modo_noturno_ativo
    total = len(lista_fotos_novas)
    cor_sucesso = "#81C784" if modo_noturno_ativo else "#2E7D32"
    cor_padrao = "#AAAAAA" if modo_noturno_ativo else "#757575"

    if total == 0:
        lbl_status_foto.config(text="Nenhuma imagem anexada", fg=cor_padrao)
    elif total == 1:
        lbl_status_foto.config(text="📸 1 Imagem anexada!", fg=cor_sucesso)
    else:
        lbl_status_foto.config(text=f"📸 {total} Imagens anexadas!", fg=cor_sucesso)


def salvar_procedimento():
    global lista_fotos_novas, id_procedimento_em_edicao, fotos_para_excluir_do_disco
    titulo = entry_titulo.get().strip()
    conteudo = text_conteudo.get("1.0", tk.END).strip()

    if not titulo or not conteudo:
        messagebox.showwarning("Aviso", "Preencha o título e o conteúdo antes de salvar!")
        return

    conn, cursor = conectar_bd()

    if id_procedimento_em_edicao is None:
        cursor.execute("INSERT INTO procedimentos (titulo, conteudo) VALUES (?, ?)", (titulo, conteudo))
        proc_id = cursor.lastrowid
        msg_sucesso = "Procedimento e fotos salvos com sucesso!"
    else:
        proc_id = id_procedimento_em_edicao
        cursor.execute("UPDATE procedimentos SET titulo=?, conteudo=? WHERE id=?", (titulo, conteudo, proc_id))
        msg_sucesso = "Procedimento atualizado com sucesso!"
        
        for foto_caminho in fotos_para_excluir_do_disco:
            cursor.execute("DELETE FROM fotos_procedimentos WHERE caminho_foto = ?", (foto_caminho,))
            if os.path.exists(foto_caminho):
                try: os.remove(foto_caminho)
                except: pass
        fotos_para_excluir_do_disco = []

    for foto_origem in lista_fotos_novas:
        if foto_origem.startswith("imagens_suporte/"):
            continue
            
        extensao = os.path.splitext(foto_origem)[1]
        nome_limpo = "".join(e for e in titulo if e.isalnum())[:15]
        foto_destino = f"imagens_suporte/{nome_limpo}_{os.urandom(4).hex()}{extensao}"
        
        try:
            shutil.copy(foto_origem, foto_destino)
            cursor.execute("INSERT INTO fotos_procedimentos (procedimento_id, caminho_foto) VALUES (?, ?)", (proc_id, foto_destino))
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar a imagem: {e}")

    conn.commit()
    conn.close()

    limpar_formulario()
    messagebox.showinfo("Sucesso", msg_sucesso)
    atualizar_lista()


def carregar_para_edicao():
    global lista_fotos_novas, id_procedimento_em_edicao, modo_noturno_ativo
    item_selecionado = lista_procedimentos.selection()
    if not item_selecionado:
        messagebox.showwarning("Aviso", "Selecione um procedimento na lista para alterar!")
        return

    limpar_formulario() 
    id_proc = lista_procedimentos.item(item_selecionado)["values"][0]

    conn, cursor = conectar_bd()
    cursor.execute("SELECT titulo, conteudo FROM procedimentos WHERE id = ?", (id_proc,))
    proc = cursor.fetchone()
    cursor.execute("SELECT caminho_foto FROM fotos_procedimentos WHERE procedimento_id = ?", (id_proc,))
    fotos = cursor.fetchall()
    conn.close()

    if proc:
        titulo, conteudo = proc
        id_procedimento_em_edicao = id_proc
        
        entry_titulo.insert(0, titulo)
        text_conteudo.insert("1.0", conteudo)
        
        lista_fotos_novas = [f[0] for f in fotos]
        atualizar_label_fotos()
            
        btn_salvar.config(text="Confirmar Alterações", bg="#1976D2")
        lbl_titulo_cadastro.config(text="✏️ Editando Procedimento")
        btn_limpar_fotos.pack(fill=tk.X, pady=5)


def excluir_procedimento():
    item_selecionado = lista_procedimentos.selection()
    if not item_selecionado:
        messagebox.showwarning("Aviso", "Selecione um procedimento na lista para excluir!")
        return

    id_proc = lista_procedimentos.item(item_selecionado)["values"][0]
    titulo_proc = lista_procedimentos.item(item_selecionado)["values"][1]

    if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja apagar:\n'{titulo_proc}'?"):
        conn, cursor = conectar_bd()
        cursor.execute("SELECT caminho_foto FROM fotos_procedimentos WHERE procedimento_id = ?", (id_proc,))
        fotos = cursor.fetchall()
        for f in fotos:
            caminho = f[0]
            if os.path.exists(caminho):
                try: os.remove(caminho)
                except: pass
                
        cursor.execute("DELETE FROM procedimentos WHERE id = ?", (id_proc,))
        cursor.execute("DELETE FROM fotos_procedimentos WHERE procedimento_id = ?", (id_proc,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Sucesso", "Procedimento excluído!")
        if id_procedimento_em_edicao == id_proc:
            limpar_formulario()
        buscar_procedimentos()


def gerenciar_limpar_fotos():
    global lista_fotos_novas, fotos_para_excluir_do_disco, id_procedimento_em_edicao
    if id_procedimento_em_edicao is not None:
        fotos_para_excluir_do_disco.extend(lista_fotos_novas)
    lista_fotos_novas = []
    atualizar_label_fotos()


def limpar_formulario():
    global lista_fotos_novas, id_procedimento_em_edicao, modo_noturno_ativo
    id_procedimento_em_edicao = None
    lista_fotos_novas = []
    entry_titulo.delete(0, tk.END)
    text_conteudo.delete("1.0", tk.END)
    atualizar_label_fotos()
    
    btn_salvar.config(text="➕ Salvar Procedimento", bg="#2E7D32" if not modo_noturno_ativo else "#388E3C")
    lbl_titulo_cadastro.config(text="📁 Cadastrar Procedimento/Erro")
    btn_limpar_fotos.pack_forget()


def buscar_procedimentos(*args):
    termo_titulo = entry_busca_titulo.get().strip()
    termo_desc = entry_busca_desc.get().strip()
    conn, cursor = conectar_bd()

    query = "SELECT id, titulo FROM procedimentos WHERE 1=1"
    parametros = []

    if termo_titulo:
        query += " AND titulo LIKE ?"
        parametros.append(f"%{termo_titulo}%")
    if termo_desc:
        query += " AND conteudo LIKE ?"
        parametros.append(f"%{termo_desc}%")

    cursor.execute(query, parametros)
    linhas = cursor.fetchall()
    conn.close()

    lista_procedimentos.delete(*lista_procedimentos.get_children())
    for linha in linhas:
        lista_procedimentos.insert("", tk.END, values=(linha[0], linha[1]))


def atualizar_lista():
    entry_busca_titulo.delete(0, tk.END)
    entry_busca_desc.delete(0, tk.END)
    buscar_procedimentos()


# --- ESTILIZAÇÃO E MODO NOTURNO ---
# --- ESTILIZAÇÃO E MODO NOTURNO ---
def alternar_modo_noturno():
    global modo_noturno_ativo
    modo_noturno_ativo = not modo_noturno_ativo

    if modo_noturno_ativo:
        # --- MODO NOTURNO ---
        cor_bg = "#121212"          
        cor_card = "#1E1E1E"        
        cor_fg = "#E0E0E0"          
        cor_input = "#2D2D2D"       
        cor_borda = "#2D2D2D"       
        cor_texto_digitacao = "#E0E0E0"
        texto_botao = "☀️ Modo Claro"
    else:
        # --- MODO CLARO (Azul Corporativo Moderno) ---
        cor_bg = "#D0E1FD"          
        cor_card = "#E3F2FD"        
        cor_fg = "#0D47A1"          
        cor_input = "#FFFFFF"       
        cor_borda = "#000000"       
        cor_texto_digitacao = "#333333" 
        texto_botao = "🌙 Modo Noturno"

    # Aplica as cores na janela principal e topo
    janela.config(bg=cor_bg)
    frame_topo.config(bg=cor_card)
    lbl_logo.config(bg=cor_card, fg=cor_fg)
    btn_modo_noturno.config(text=texto_botao, bg=cor_bg, fg=cor_fg)

    # Aplica as cores nos painéis (cards) principais
    card_cadastro.config(bg=cor_card)
    card_busca.config(bg=cor_card)
    frame_botoes_acao.config(bg=cor_card)

    # CORREÇÃO: Força os frames de filtro de busca a também terem a cor azul correta
    try:
        frame_filtros.config(bg=cor_card)
        frame_filtro1.config(bg=cor_card)
        frame_filtro2.config(bg=cor_card)
    except:
        pass

    # Atualiza as labels (textos fixos) dentro dos cards
    for widget in card_cadastro.winfo_children() + card_busca.winfo_children():
        if isinstance(widget, tk.Label) and widget != lbl_status_foto:
            widget.config(bg=cor_card, fg=cor_fg)
            
    # CORREÇÃO ADICIONAL: Garante que as labels escondidas dentro dos mini-frames também fiquem azuis
    try:
        for w in frame_filtro1.winfo_children() + frame_filtro2.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=cor_card, fg=cor_fg)
    except:
        pass

    # Garante o padrão correto em todos os inputs do sistema
    for entry in [entry_titulo, entry_busca_titulo, entry_busca_desc]:
        entry.config(
            bg=cor_input, 
            fg=cor_texto_digitacao, 
            insertbackground=cor_fg,
            highlightbackground=cor_borda,  
            highlightcolor=cor_borda,        
            highlightthickness=1             
        )
        
    text_conteudo.config(
        bg=cor_input, 
        fg=cor_texto_digitacao, 
        insertbackground=cor_fg,
        highlightbackground=cor_borda,      
        highlightcolor=cor_borda,            
        highlightthickness=1                 
    )

    # Botões secundários
    btn_foto.config(bg=cor_bg, fg=cor_fg)
    btn_cancelar_edicao.config(bg=cor_bg, fg=cor_fg)

    # Atualiza a cor do botão Salvar
    atualizar_label_fotos()
    if id_procedimento_em_edicao is None:
        btn_salvar.config(bg="#388E3C" if modo_noturno_ativo else "#1565C0")
    else:
        btn_salvar.config(bg="#1A365D" if modo_noturno_ativo else "#1976D2")

    # Estilização moderna da tabela (Treeview)
    style = ttk.Style()
    style.theme_use("clam")
    if modo_noturno_ativo:
        style.configure("Treeview", background="#2D2D2D", fieldbackground="#2D2D2D", foreground="#FFFFFF", rowheight=28)
        style.configure("Treeview.Heading", background="#121212", foreground="#FFFFFF", borderwidth=0, font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#1976D2')])
    else:
        style.configure("Treeview", background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#333333", rowheight=28)
        style.configure("Treeview.Heading", background="#BBDEFB", foreground="#0D47A1", borderwidth=0, font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#90CAF9')], foreground=[('selected', '#000000')])


def ver_detalhes(event):
    global modo_noturno_ativo
    item_selecionado = lista_procedimentos.selection()
    if not item_selecionado: return

    id_proc = lista_procedimentos.item(item_selecionado)["values"][0]
    conn, cursor = conectar_bd()
    cursor.execute("SELECT titulo, conteudo FROM procedimentos WHERE id = ?", (id_proc,))
    proc = cursor.fetchone()
    cursor.execute("SELECT caminho_foto FROM fotos_procedimentos WHERE procedimento_id = ?", (id_proc,))
    fotos = cursor.fetchall()
    conn.close()

    if not proc: return
    titulo, conteudo = proc

    if modo_noturno_ativo:
        cor_bg = "#1E1E1E" 
        cor_fg = "#E0E0E0" 
        cor_txt_bg = "#2D2D2D"
        cor_borda = "#2D2D2D"
    else:
        cor_bg = "#E3F2FD"         
        cor_fg = "#0D47A1"         
        cor_txt_bg = "#FFFFFF"     
        cor_borda = "#000000"      

    janela_detalhes = tk.Toplevel(janela)
    janela_detalhes.title(titulo)
    janela_detalhes.state('zoomed')  
    janela_detalhes.config(bg=cor_bg)

    # Criando o Canvas e a Scrollbar Geral da Página
    canvas = tk.Canvas(janela_detalhes, borderwidth=0, bg=cor_bg, highlightthickness=0)
    scrollbar_geral = ttk.Scrollbar(janela_detalhes, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=cor_bg)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar_geral.set)
    
    scrollbar_geral.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Rolagem global da página com o mouse wheel
    def _ao_rolar_mouse(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    janela_detalhes.bind_all("<MouseWheel>", _ao_rolar_mouse)

    def ajustar_largura_responsiva(event):
        largura_janela = event.width
        canvas.itemconfig(canvas_frame_id, width=largura_janela)
        lbl_titulo.config(wraplength=largura_janela - 60)

    canvas.bind("<Configure>", ajustar_largura_responsiva)

    # Título
    lbl_titulo = tk.Label(scrollable_frame, text=titulo, font=("Arial", 16, "bold"), bg=cor_bg, fg=cor_fg, justify=tk.LEFT)
    lbl_titulo.pack(pady=20, padx=30, fill=tk.X, anchor=tk.W)
    
    tk.Label(scrollable_frame, text="📋 Solução / Passo a Passo:", font=("Arial", 11, "bold"), bg=cor_bg, fg=cor_fg).pack(padx=30, anchor=tk.W)

    # --- NOVO: CONTAINER COMPACTO PARA A SOLUÇÃO COM SUA PRÓPRIA BARRA ---
    frame_texto_solucao = tk.Frame(scrollable_frame, bg=cor_borda, bd=1) # Cria uma borda preta em volta de tudo
    frame_texto_solucao.pack(fill=tk.X, padx=30, pady=5)

    # Barra de rolagem dedicada interna da Solução
    scrollbar_interna = ttk.Scrollbar(frame_texto_solucao, orient="vertical")
    
    # Caixa de texto com tamanho fixado em 18 linhas para forçar a barra a aparecer se o texto crescer
    txt = tk.Text(
        frame_texto_solucao, 
        wrap=tk.WORD, 
        height=18, 
        font=("Arial", 11), 
        bg=cor_txt_bg, 
        fg="#333333" if not modo_noturno_ativo else cor_fg, 
        padx=12, 
        pady=12, 
        bd=0,
        yscrollcommand=scrollbar_interna.set
    )
    
    scrollbar_interna.config(command=txt.yview)
    
    # Organiza lado a lado dentro do frame dedicado
    scrollbar_interna.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)

    txt.insert(tk.END, conteudo)
    txt.config(state=tk.DISABLED)

    # --- CONTROLE TÉCNICO DE ROLAGEM DO MOUSE ---
    # Quando o mouse estiver em cima do texto, roda apenas a Solução se ela tiver rolagem.
    # Se chegar no fim do texto, o sinal "break" evita que a página corra desordenada.
    def _rolar_texto_interno(event):
        txt.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
        
    txt.bind("<MouseWheel>", _rolar_texto_interno)

    janela_detalhes.images_refs = []  
    if fotos:
        tk.Label(scrollable_frame, text="📸 Imagens de Suporte:", font=("Arial", 11, "bold"), bg=cor_bg, fg=cor_fg).pack(padx=30, pady=(20, 5), anchor=tk.W)
        for index, f in enumerate(fotos, 1):
            caminho_foto = f[0]
            if os.path.exists(caminho_foto):
                try:
                    img = Image.open(caminho_foto)
                    img.thumbnail((1200, 700)) 
                    img_tk = ImageTk.PhotoImage(img)

                    lbl_text_print = tk.Label(scrollable_frame, text=f"Print #{index}", font=("Arial", 9, "italic"), fg="gray", bg=cor_bg)
                    lbl_text_print.pack(anchor=tk.W, padx=30, pady=(10,0))
                    
                    lbl_img = tk.Label(scrollable_frame, image=img_tk, bg=cor_bg, bd=1, relief="solid")
                    lbl_img.pack(pady=5, padx=30, anchor=tk.W)
                    janela_detalhes.images_refs.append(img_tk)
                except:
                    pass


# --- LAYOUT DA INTERFACE (DASHBOARD) ---
janela = tk.Tk()
janela.title("Repositório de TI - Documentação e Erros")
janela.geometry("1000x680")  
janela.state('zoomed')

# 1. BARRA DE TOPO (Header Fixo)
frame_topo = tk.Frame(janela, height=60, bd=0, relief="flat")
frame_topo.pack(side=tk.TOP, fill=tk.X)
frame_topo.pack_propagate(False)

lbl_logo = tk.Label(frame_topo, text="🔧 REPOSITÓRIO DE TI", font=("Arial", 14, "bold"))
lbl_logo.pack(side=tk.LEFT, padx=20)

btn_modo_noturno = tk.Button(frame_topo, text="🌙 Modo Noturno", font=("Arial", 9, "bold"), command=alternar_modo_noturno, bd=0, padx=10, pady=5)
btn_modo_noturno.pack(side=tk.RIGHT, padx=20)

# Container Principal
container_corpo = tk.Frame(janela, bg="")
container_corpo.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

# 2. PAINEL DA ESQUERDA: Cadastro
card_cadastro = tk.Frame(container_corpo, padx=15, pady=15, width=350)
card_cadastro.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
card_cadastro.pack_propagate(False) 

lbl_titulo_cadastro = tk.Label(card_cadastro, text="📁 Cadastrar Procedimento/Erro", font=("Arial", 11, "bold"))
lbl_titulo_cadastro.pack(anchor=tk.W, pady=(0, 15))

tk.Label(card_cadastro, text="Título ou Palavra-chave do Erro:", font=("Arial", 9)).pack(anchor=tk.W, pady=(5, 2))
entry_titulo = tk.Entry(card_cadastro, font=("Arial", 11), bd=0)
entry_titulo.pack(fill=tk.X, pady=2, ipady=4)

tk.Label(card_cadastro, text="Solução (Passo a Passo):", font=("Arial", 9)).pack(anchor=tk.W, pady=(10, 2))
text_conteudo = tk.Text(card_cadastro, wrap=tk.WORD, height=10, font=("Arial", 10), bd=0, padx=5, pady=5)
text_conteudo.pack(fill=tk.BOTH, expand=True, pady=2)

btn_foto = tk.Button(card_cadastro, text="📸 Anexar Imagens/Prints", command=selecionar_fotos, bd=0, pady=5)
btn_foto.pack(fill=tk.X, pady=(10, 2))

lbl_status_foto = tk.Label(card_cadastro, text="Nenhuma imagem anexada", font=("Arial", 9))
lbl_status_foto.pack(anchor=tk.W, pady=2)

btn_limpar_fotos = tk.Button(card_cadastro, text="🗑️ Remover Todas as Fotos", command=gerenciar_limpar_fotos, fg="#D32F2F", bd=0)

btn_salvar = tk.Button(card_cadastro, text="➕ Salvar Procedimento", command=salvar_procedimento, fg="white", font=("Arial", 10, "bold"), bd=0, pady=6)
btn_salvar.pack(fill=tk.X, pady=(15, 5))

btn_cancelar_edicao = tk.Button(card_cadastro, text="Limpar Campos / Novo", command=limpar_formulario, bd=0, pady=4)
btn_cancelar_edicao.pack(fill=tk.X, pady=2)


# Espaçador entre os cards
tk.Frame(container_corpo, width=15, bg="").pack(side=tk.LEFT, fill=tk.Y)


# 3. PAINEL DA DIREITA: Busca e Tabela
card_busca = tk.Frame(container_corpo, padx=15, pady=15)
card_busca.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

lbl_titulo_busca = tk.Label(card_busca, text="🔍 Consultar Painel de Erros", font=("Arial", 11, "bold"))
lbl_titulo_busca.pack(anchor=tk.W, pady=(0, 15))

# Filtros de Busca LADO A LADO
frame_filtros = tk.Frame(card_busca, bg="")
frame_filtros.pack(fill=tk.X, pady=(0, 10))

frame_filtro1 = tk.Frame(frame_filtros, bg="")
frame_filtro1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
tk.Label(frame_filtro1, text="Pesquisar por Título:", font=("Arial", 9)).pack(anchor=tk.W)
entry_busca_titulo = tk.Entry(frame_filtro1, font=("Arial", 10), bd=0)
entry_busca_titulo.pack(fill=tk.X, pady=2, ipady=4)
entry_busca_titulo.bind("<KeyRelease>", buscar_procedimentos)

frame_filtro2 = tk.Frame(frame_filtros, bg="")
frame_filtro2.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
tk.Label(frame_filtro2, text="Pesquisar pela Solução (Texto):", font=("Arial", 9)).pack(anchor=tk.W)
entry_busca_desc = tk.Entry(frame_filtro2, font=("Arial", 10), bd=0)
entry_busca_desc.pack(fill=tk.X, pady=2, ipady=4)
entry_busca_desc.bind("<KeyRelease>", buscar_procedimentos)

# Tabela Configurada
colunas = ("id", "titulo")
lista_procedimentos = ttk.Treeview(card_busca, columns=colunas, show="headings")
lista_procedimentos.heading("id", text="ID")
lista_procedimentos.heading("titulo", text="Procedimento / Erro Cadastrado")

lista_procedimentos.column("id", width=60, minwidth=50, anchor=tk.CENTER)
lista_procedimentos.column("titulo", width=400, anchor=tk.W)
lista_procedimentos.pack(fill=tk.BOTH, expand=True, pady=5)

lista_procedimentos.bind("<Double-1>", ver_detalhes)

# Botões de Ação embaixo da tabela
frame_botoes_acao = tk.Frame(card_busca)
frame_botoes_acao.pack(fill=tk.X, pady=(10, 0))

btn_alterar = tk.Button(frame_botoes_acao, text="✏️ Editar Selecionado", command=carregar_para_edicao, bg="#FF9800", fg="white", font=("Arial", 9, "bold"), bd=0, pady=6)
btn_alterar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

btn_excluir = tk.Button(frame_botoes_acao, text="❌ Excluir Registro", command=excluir_procedimento, bg="#D32F2F", fg="white", font=("Arial", 9, "bold"), bd=0, pady=6)
btn_excluir.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))

# Inicialização padrão do Modo Claro
modo_noturno_ativo = True
alternar_modo_noturno()

buscar_procedimentos()
janela.mainloop()