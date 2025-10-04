# Projeto AcordoCobrança

Pequeno sistema Flask para gerir acordos de cobrança.

Setup rápido:

1. Criar e ativar virtualenv (Windows PowerShell):

   python -m venv .venv; .\.venv\Scripts\Activate.ps1

2. Instalar dependências:

   pip install -r requirements.txt

3. Variáveis de ambiente recomendadas:

   $env:FLASK_SECRET_KEY = 'uma_chave_segura'

4. Rodar a aplicação:

   python main.py

Commit & push para GitHub:

1. git init
2. git add .
3. git commit -m "Inicial commit"
4. Criar repositório no GitHub e seguir instruções para adicionar remote e push

Testando o autocomplete de credor (passo a passo)
-----------------------------------------------

Observação: a rota que fornece a lista de credores (`/listar_credor`) está protegida por login. Não remova essa proteção — siga os passos abaixo para testar enquanto estiver autenticado.

1) Preparar ambiente (PowerShell)

   python -m venv .venv; .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   $env:FLASK_SECRET_KEY = 'uma_chave_segura'

2) Rodar a aplicação

   python main.py

3) No navegador (teste manual)

   - Acesse http://127.0.0.1:5000/login e faça login com um usuário válido do sistema.
   - Depois de logado, abra http://127.0.0.1:5000/cliente

4) Verificar requisição do autocomplete (DevTools)

   - Abra as Ferramentas de Desenvolvedor (F12) → aba Network.
   - No campo de filtro digite `listar_credor` para encontrar a requisição.
   - Recarregue a página (F5). A requisição `/listar_credor` deve ser enviada automaticamente pelo JS.
   - Verifique:
     - Status HTTP: 200
     - Response: JSON no formato {"credor": [{"codigo":"...","nome":"..."}, ...]}

5) Se a requisição retornar HTML (login) ou 302:

   - Significa que a sessão não foi enviada ou expirou. Verifique:
     - Você está logado no mesmo domínio (127.0.0.1:5000).
     - Cookies habilitados e não bloqueados por extensões.
     - No arquivo `templates/cliente.html` o fetch usa `credentials: 'same-origin'` (deveria estar configurado).

6) Comandos de diagnóstico (no servidor)

   - Listar rotas registradas (no workspace):

     python -c "import importlib; m=importlib.import_module('app'); print(sorted([r.rule for r in m.app.url_map.iter_rules()]))"

     Deve listar `/listar_credor` e `/buscar_credor`.

   - Testar rota com sessão simulada (não inicia servidor):

     python -c "import importlib; m=importlib.import_module('app'); c=m.app.test_client();\
with c.session_transaction() as s: s['usuario_autenticado']='teste';\
print(c.get('/listar_credor').get_data(as_text=True))"

     Isso imprime o JSON que a rota retornaria para um usuário autenticado.

7) Se ainda não funcionar

   - Verifique logs do servidor (onde executou `python main.py`) para erros.
   - Confirme que a tabela `credores` em `partes_demo.db` contém registros válidos com o campo `codigo` preenchido.
   - Se quiser, posso criar um pequeno endpoint temporário não protegido para teste, mas por segurança não recomendarei que fique permanente.

Se quiser, adiciono estas instruções também em uma seção "Troubleshooting" com capturas de tela e exemplos de respostas.

