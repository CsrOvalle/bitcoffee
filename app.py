https://github.com/CsrOvalle/bitcoffee/blob/main/app.py

    st.button("Alertas do sistema", use_container_width=True, key="alertas_sistema")
    if st.button("Sair da administração", key="sair_administracao"):
        sair_da_conta()

elif st.session_state.tela_atual == "TELA302 - ESTOQUE":
    if st.button("← Menu principal", key="menu_principal_estoque"):
        navegar_para(TELA_INICIAL)
    if not usuario_e_administrador():
        st.error("Acesso restrito. Entre como administrador para abrir o estoque.")
        if st.button("Ir para login administrativo", key="ir_login_admin_estoque_bloqueado"):
            navegar_para("TELA300 - LOGIN ADMINISTRADOR")
        st.stop()
    st.title("☕ Bitcoffee")
    st.write(f"Perfil: **{st.session_state.usuario_logado}**")
    st.subheader("Controle de Estoque")

    for produto in PRODUTOS:
        coluna_imagem, coluna_dados, coluna_preco = st.columns([1, 3, 2])
        with coluna_imagem:
            imagem_generica("CAFÉ", 90)
        with coluna_dados:
            st.write(f"**Nome:** {produto['nome']}")
            st.write(f"**ID:** {produto['id']}")
            st.write("Quantidade em estoque: 15")
        with coluna_preco:
            st.number_input(
                "Preço unitário",
                value=float(produto["preco"]),
                min_value=0.0,
                step=0.50,
                key=f"preco_estoque_{produto['id']}",
            )
        st.divider()

    coluna_desfazer, coluna_registrar = st.columns(2)
    with coluna_desfazer:
        if st.button("Desfazer", key="desfazer_estoque"):
            st.toast("Alterações desfeitas.")
    with coluna_registrar:
        if st.button("Registrar alterações", key="registrar_estoque"):
            st.success("Estoque atualizado com sucesso!")
