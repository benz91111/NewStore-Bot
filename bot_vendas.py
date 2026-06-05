import discord
from discord import app_commands
from discord.ui import Select, View, Modal, TextInput, Button
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURACOES =====
TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "produtos.json"
PAINEL_FILE = "paineis.json"
TICKETS_FILE = "tickets.json"
CARRINHOS_FILE = "carrinhos.json"

# IDs fixos
STAFF_ROLE_ID = 1512273191152783410
VENDAS_CANAL_ID = 1512216907863036125
CATEGORIA_CARRINHOS_ID = 1512462336227545339

# ===== EMOJIS CUSTOMIZADOS DO SERVIDOR =====
E = {
    "carrinho": "<:emoji_5:1512454950750388254>",
    "usuario": "<:emoji_11:1512455369581133986>",
    "produto": "<:emoji_5:1512454991300788276>",
    "preco": "<:emoji_18:1512456019303727327>",
    "descricao": "<:emoji_17:1512455949657313463>",
    "status": "<a:emoji_19:1512456283393888296>",
    "footer": "<:emoji_20:1512460884222415049>",
    "confirmar": "<:emoji_27:1512470826136375508>",
    "lixeira": "<:emoji_27:1512470826136375508>",
    "editar": "<:emoji_27:1512470826136375508>",
    "voltar": "<:emoji_29:1512475548683599902>",
    "adicionar": "<:emoji_29:1512475548683599902>",
    "logo": "<:emoji_30:1512478785495240715>",
    "menos": "<:emoji_22:1512465220642144366>",
    "lapis": "<:emoji_25:1512468439548035252>",
    "mais": "<:emoji_23:1512465281815941200>",
    "lixeira_carrinho": "<:emoji_26:1512469123211329817>",
    "pagamento": "<:emoji_7:1512455033415798886>",
    "valor": "<:emoji_8:1512455082145349702>",
    "quantidade": "<:emoji_21:1512464919625465916>",
    "disponivel": "<:emoji_24:1512466459832614993>",
}

# ===== EMOJIS DE MARCAS (PRODUTOS) =====
EMOJIS_MARCAS = {
    "netflix": "<:emoji_30:1512511475963396178>",
    "crunchyroll": "<:emoji_31:1512511500676235315>",
    "hbo max": "<:emoji_33:1512512537823023244>",
    "prime video": "<:emoji_34:1512512868623323191>",
    "disney": "<:emoji_32:1512512515525836892>",
    "paramount": "<:emoji_35:1512512887321526393>",
}

def detectar_emoji_produto(nome_produto):
    """Detecta automaticamente o emoji baseado no nome do produto"""
    nome_lower = nome_produto.lower()
    for marca, emoji in EMOJIS_MARCAS.items():
        if marca in nome_lower:
            return emoji
    return E["produto"]

# ===== IMAGENS DO IMGUR =====
IMG = {
    "banner": "https://i.imgur.com/jDo23VT.png",
    "forbidden": "https://i.imgur.com/GH72rDY.png",
    "delete": "https://i.imgur.com/U10LD6r.png",
    "correct": "https://i.imgur.com/iBQmtbf.png",
    "double_check": "https://i.imgur.com/3mQVp90.png",
    "nubank": "https://i.imgur.com/z7OYi2n.png",
    "cart": "https://i.imgur.com/uNzcFQG.png",
    "cardbox": "https://i.imgur.com/b9yyfwZ.png",
    "hammer": "https://i.imgur.com/2h5uqCc.png",
}

# ===== FUNCOES AUXILIARES =====
def carregar_json(arquivo, default=None):
    if default is None:
        default = {}
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

produtos = carregar_json(DATA_FILE)
paineis = carregar_json(PAINEL_FILE)
tickets = carregar_json(TICKETS_FILE, default=[])
carrinhos = carregar_json(CARRINHOS_FILE, default={})

# ===== BOT =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== MODAIS =====
class ProdutoModal(Modal, title="Adicionar Produto"):
    nome = TextInput(label="Nome do produto", placeholder="Ex: Netflix Premium", max_length=50)
    descricao = TextInput(label="Descricao", style=discord.TextStyle.paragraph, placeholder="Descricao...", max_length=400)
    preco = TextInput(label="Preco", placeholder="Ex: R$ 15,00", max_length=20)
    quantidade = TextInput(label="Quantidade em estoque", placeholder="Ex: 10", max_length=10)
    categoria = TextInput(label="Categoria (opcional)", placeholder="Ex: Contas", required=False, max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value.strip())
            if qtd < 0:
                await interaction.response.send_message("Quantidade nao pode ser negativa!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Quantidade precisa ser um numero inteiro!", ephemeral=True)
            return

        canal_id = str(interaction.channel_id)
        if canal_id not in produtos:
            produtos[canal_id] = []

        emoji_produto = detectar_emoji_produto(self.nome.value.strip())

        produto_id = len(produtos[canal_id]) + 1
        produto = {
            "id": produto_id,
            "nome": self.nome.value.strip(),
            "descricao": self.descricao.value.strip(),
            "preco": self.preco.value.strip(),
            "quantidade": qtd,
            "categoria": self.categoria.value.strip() if self.categoria.value else "Geral",
            "vendidos": 0,
            "emoji": emoji_produto
        }
        produtos[canal_id].append(produto)
        salvar_json(DATA_FILE, produtos)
        await atualizar_painel(interaction.channel)

        embed = discord.Embed(title="Produto Adicionado!", description="**" + produto['nome'] + "** adicionado!", color=discord.Color.green())
        embed.set_thumbnail(url=IMG["correct"])
        embed.add_field(name="Preco", value=produto['preco'], inline=True)
        embed.add_field(name="Estoque", value=str(produto['quantidade']), inline=True)
        embed.add_field(name="Categoria", value=produto['categoria'], inline=True)
        embed.add_field(name="Emoji", value=produto['emoji'], inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class EditarProdutoModal(Modal, title="Editar Produto"):
    def __init__(self, produto_id, canal_id):
        super().__init__()
        self.produto_id = produto_id
        self.canal_id = canal_id
        prod = next((p for p in produtos.get(canal_id, []) if p['id'] == produto_id), None)
        if prod:
            self.nome.default = prod['nome']
            self.descricao.default = prod['descricao']
            self.preco.default = prod['preco']
            self.quantidade.default = str(prod['quantidade'])
            self.categoria.default = prod['categoria']
            self.emoji.default = prod.get('emoji', detectar_emoji_produto(prod['nome']))

    nome = TextInput(label="Nome", max_length=50)
    descricao = TextInput(label="Descricao", style=discord.TextStyle.paragraph, max_length=400)
    preco = TextInput(label="Preco", max_length=20)
    quantidade = TextInput(label="Quantidade", max_length=10)
    categoria = TextInput(label="Categoria", required=False, max_length=30)
    emoji = TextInput(label="Emoji (opcional)", placeholder="Ex: <:netflix:123456789>", required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value.strip())
            if qtd < 0:
                await interaction.response.send_message("Quantidade nao pode ser negativa!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Quantidade precisa ser um numero inteiro!", ephemeral=True)
            return

        for p in produtos.get(self.canal_id, []):
            if p['id'] == self.produto_id:
                p['nome'] = self.nome.value.strip()
                p['descricao'] = self.descricao.value.strip()
                p['preco'] = self.preco.value.strip()
                p['quantidade'] = qtd
                p['categoria'] = self.categoria.value.strip() if self.categoria.value else "Geral"
                if self.emoji.value and self.emoji.value.strip():
                    p['emoji'] = self.emoji.value.strip()
                else:
                    p['emoji'] = detectar_emoji_produto(p['nome'])
                break
        salvar_json(DATA_FILE, produtos)
        channel = bot.get_channel(int(self.canal_id))
        if channel:
            await atualizar_painel(channel)
        await interaction.response.send_message("Produto editado!", ephemeral=True)

class PainelModal(Modal, title="Configurar Painel"):
    titulo = TextInput(label="Titulo", placeholder="Ex: Loja de Contas", max_length=100)
    descricao = TextInput(label="Descricao", style=discord.TextStyle.paragraph, placeholder="Bem-vindo...", max_length=500)
    cor = TextInput(label="Cor (hex)", placeholder="Ex: #820AD1", required=False, max_length=7)
    imagem = TextInput(label="URL imagem (opcional)", placeholder="https://...", required=False, max_length=200)
    footer = TextInput(label="Rodape (opcional)", placeholder="Clique abaixo para comprar", required=False, max_length=100)

    async def on_submit(self, interaction: discord.Interaction):
        canal_id = str(interaction.channel_id)
        try:
            cor = int(self.cor.value.replace("#", ""), 16) if self.cor.value else 0x820AD1
        except:
            cor = 0x820AD1
        paineis[canal_id] = {
            "titulo": self.titulo.value.strip(),
            "descricao": self.descricao.value.strip(),
            "cor": cor,
            "imagem": self.imagem.value.strip() if self.imagem.value else None,
            "footer": self.footer.value.strip() if self.footer.value else None
        }
        salvar_json(PAINEL_FILE, paineis)
        await interaction.response.send_message("Painel configurado! Use /painel para enviar.", ephemeral=True)

class QuantidadeModal(Modal, title="Quantidade Desejada"):
    quantidade = TextInput(label="Quantidade", placeholder="Ex: 2", max_length=5)

    def __init__(self, carrinho_id):
        super().__init__()
        self.carrinho_id = carrinho_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value.strip())
            if qtd < 1:
                await interaction.response.send_message("Quantidade invalida!", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("Digite um numero valido!", ephemeral=True)
            return

        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            await interaction.response.send_message("Carrinho nao encontrado!", ephemeral=True)
            return

        prod = next((p for p in produtos.get(carrinho['canal_id'], []) if p['id'] == carrinho['produto_id']), None)
        if not prod:
            await interaction.response.send_message("Produto nao encontrado!", ephemeral=True)
            return

        if qtd > prod['quantidade']:
            await interaction.response.send_message("Quantidade maior que o estoque disponivel! Estoque: " + str(prod['quantidade']), ephemeral=True)
            return

        carrinho['quantidade_desejada'] = qtd
        salvar_json(CARRINHOS_FILE, carrinhos)

        canal = bot.get_channel(int(self.carrinho_id))
        if canal:
            await atualizar_embed_carrinho(canal, carrinho)

        await interaction.response.send_message("Quantidade atualizada para " + str(qtd) + "!", ephemeral=True)

# ===== BOTOES DO CARRINHO =====
class MenosButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(emoji=E["menos"], style=discord.ButtonStyle.secondary)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            return
        if carrinho['quantidade_desejada'] > 1:
            carrinho['quantidade_desejada'] -= 1
            salvar_json(CARRINHOS_FILE, carrinhos)
            canal = bot.get_channel(int(self.carrinho_id))
            if canal:
                await atualizar_embed_carrinho(canal, carrinho)
        await interaction.response.defer()

class LapisButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(emoji=E["lapis"], style=discord.ButtonStyle.primary)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(QuantidadeModal(self.carrinho_id))

class MaisButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(emoji=E["mais"], style=discord.ButtonStyle.secondary)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            return
        prod = next((p for p in produtos.get(carrinho['canal_id'], []) if p['id'] == carrinho['produto_id']), None)
        if prod and carrinho['quantidade_desejada'] < prod['quantidade']:
            carrinho['quantidade_desejada'] += 1
            salvar_json(CARRINHOS_FILE, carrinhos)
            canal = bot.get_channel(int(self.carrinho_id))
            if canal:
                await atualizar_embed_carrinho(canal, carrinho)
        await interaction.response.defer()

class RemoverButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(emoji=E["lixeira_carrinho"], style=discord.ButtonStyle.danger)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        carrinho = carrinhos.get(self.carrinho_id)
        if carrinho:
            canal = bot.get_channel(int(self.carrinho_id))
            if canal:
                await canal.delete()
            if self.carrinho_id in carrinhos:
                del carrinhos[self.carrinho_id]
                salvar_json(CARRINHOS_FILE, carrinhos)
        await interaction.response.defer()

class PagamentoButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(label="Ir para o Pagamento", emoji=E["pagamento"], style=discord.ButtonStyle.success)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            await interaction.response.send_message("Carrinho nao encontrado!", ephemeral=True)
            return

        prod = next((p for p in produtos.get(carrinho['canal_id'], []) if p['id'] == carrinho['produto_id']), None)
        if not prod:
            await interaction.response.send_message("Produto nao encontrado!", ephemeral=True)
            return

        try:
            preco_limpo = prod['preco'].replace("R$", "").replace("$", "").replace(",", ".").strip()
            total = float(preco_limpo) * carrinho['quantidade_desejada']
            total_str = "R$ " + str(total)
        except:
            total_str = prod['preco'] + " x " + str(carrinho['quantidade_desejada'])

        dm_embed = discord.Embed(
            title=E["carrinho"] + " **New Store | Pagamento**",
            description="Resumo da sua compra:",
            color=0x820AD1
        )
        dm_embed.add_field(name=E["produto"] + " Produto", value="**" + prod['nome'] + "**", inline=False)
        dm_embed.add_field(name=E["valor"] + " Valor Unitario", value="`" + prod['preco'] + "`", inline=True)
        dm_embed.add_field(name=E["quantidade"] + " Quantidade", value="`" + str(carrinho['quantidade_desejada']) + "`", inline=True)
        dm_embed.add_field(name=E["preco"] + " Total", value="`" + total_str + "`", inline=False)
        dm_embed.set_footer(text="Clique no botao abaixo para ver a chave Pix", icon_url=IMG["nubank"])

        view = View()
        view.add_item(PixButton(self.carrinho_id))
        view.add_item(PagamentoEfetuadoButton(self.carrinho_id))

        await interaction.user.send(embed=dm_embed, view=view)
        await interaction.response.send_message("Enviei os dados de pagamento na sua DM!", ephemeral=True)

class ConfirmarCarrinhoButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(label="Confirmar Compra", emoji=E["confirmar"], style=discord.ButtonStyle.success)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message("Apenas Staff pode confirmar!", ephemeral=True)
            return

        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            await interaction.response.send_message("Carrinho nao encontrado!", ephemeral=True)
            return

        if carrinho.get('status') == "confirmado":
            await interaction.response.send_message("Esta compra ja foi confirmada!", ephemeral=True)
            return

        prod = next((p for p in produtos.get(carrinho['canal_id'], []) if p['id'] == carrinho['produto_id']), None)
        if not prod:
            await interaction.response.send_message("Produto nao encontrado!", ephemeral=True)
            return

        carrinho['status'] = "confirmado"
        carrinho['staff_id'] = interaction.user.id
        carrinho['staff_name'] = interaction.user.name
        salvar_json(CARRINHOS_FILE, carrinhos)

        qtd = carrinho.get('quantidade_desejada', 1)
        for p in produtos.get(carrinho['canal_id'], []):
            if p['id'] == carrinho['produto_id']:
                p['quantidade'] -= qtd
                p['vendidos'] += qtd
                break
        salvar_json(DATA_FILE, produtos)

        channel = bot.get_channel(int(carrinho['canal_id']))
        if channel:
            await atualizar_painel(channel)

        embed = discord.Embed(
            title=E["confirmar"] + " **Compra Confirmada!**",
            description="Carrinho confirmado por " + interaction.user.mention,
            color=discord.Color.green()
        )
        embed.add_field(name=E["usuario"] + " Cliente", value="<@" + str(carrinho['user_id']) + "> (" + carrinho['user_name'] + ")", inline=True)
        embed.add_field(name=E["produto"] + " Produto", value=prod['nome'], inline=True)
        embed.add_field(name=E["quantidade"] + " Quantidade", value=str(qtd), inline=True)
        embed.add_field(name=E["preco"] + " Preco", value=prod['preco'], inline=True)
        embed.set_footer(text="Confirmado por: " + interaction.user.name, icon_url=IMG["double_check"])
        await interaction.response.send_message(embed=embed)

        vendas_channel = bot.get_channel(VENDAS_CANAL_ID)
        if vendas_channel:
            vendas_embed = discord.Embed(title="Venda Finalizada!", description="Nova venda confirmada!", color=0x820AD1)
            vendas_embed.set_author(name="New Store", icon_url=IMG["nubank"])
            vendas_embed.add_field(name="Usuario", value="`" + carrinho['user_name'] + "`", inline=True)
            vendas_embed.add_field(name="Produto", value="`" + prod['nome'] + "`", inline=True)
            vendas_embed.add_field(name="Quantidade", value="`" + str(qtd) + "`", inline=True)
            vendas_embed.add_field(name="Preco", value="`" + prod['preco'] + "`", inline=True)
            vendas_embed.add_field(name="Staff", value="`" + interaction.user.name + "`", inline=True)
            vendas_embed.add_field(name="Data", value="`" + discord.utils.utcnow().strftime('%d/%m/%Y %H:%M') + "`", inline=True)
            vendas_embed.set_footer(text="Vem Decolar, Vem com a New Store!", icon_url=IMG["nubank"])
            vendas_embed.set_image(url=IMG["banner"])
            await vendas_channel.send(embed=vendas_embed)

        import asyncio
        await asyncio.sleep(10)
        canal = bot.get_channel(int(self.carrinho_id))
        if canal:
            await canal.delete()
        if self.carrinho_id in carrinhos:
            del carrinhos[self.carrinho_id]
            salvar_json(CARRINHOS_FILE, carrinhos)

class PixButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(label="Pix Copia e Cola", emoji=E["confirmar"], style=discord.ButtonStyle.primary)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        pix_embed = discord.Embed(
            title=E["carrinho"] + " **Chave Pix**",
            description="```21985515969```",
            color=0x820AD1
        )
        pix_embed.add_field(name="Nome", value="Miguel Henrique", inline=False)
        pix_embed.add_field(name="Tipo", value="Telefone", inline=False)
        pix_embed.set_footer(text="Copie a chave acima e faca o pagamento no seu banco!")
        await interaction.response.send_message(embed=pix_embed, ephemeral=True)

class PagamentoEfetuadoButton(Button):
    def __init__(self, carrinho_id):
        super().__init__(label="Ja efetuei o pagamento", style=discord.ButtonStyle.success)
        self.carrinho_id = carrinho_id

    async def callback(self, interaction: discord.Interaction):
        carrinho = carrinhos.get(self.carrinho_id)
        if not carrinho:
            await interaction.response.send_message("Carrinho nao encontrado!", ephemeral=True)
            return

        canal = bot.get_channel(int(self.carrinho_id))
        if canal:
            await canal.send("**" + interaction.user.mention + "** ja efetuou o pagamento! Favor enviar o comprovante aqui e aguardar a confirmacao da Staff.")

        await interaction.response.send_message("Notificacao enviada! Aguarde a confirmacao da Staff.", ephemeral=True)

class ConfirmarCompraButton(Button):
    def __init__(self, ticket_id):
        super().__init__(label="Confirmar Compra", emoji=E["confirmar"], style=discord.ButtonStyle.success)
        self.ticket_id = ticket_id

    async def callback(self, interaction: discord.Interaction):
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message("Apenas Staff pode confirmar!", ephemeral=True)
            return

        ticket = next((t for t in tickets if t['id'] == self.ticket_id), None)
        if not ticket:
            await interaction.response.send_message("Ticket nao encontrado!", ephemeral=True)
            return
        if ticket['status'] == "confirmado":
            await interaction.response.send_message("Ja confirmado!", ephemeral=True)
            return

        ticket['status'] = "confirmado"
        ticket['staff_id'] = interaction.user.id
        ticket['staff_name'] = interaction.user.name
        salvar_json(TICKETS_FILE, tickets)

        canal_id = str(ticket['canal_id'])
        for p in produtos.get(canal_id, []):
            if p['id'] == ticket['produto_id']:
                p['quantidade'] -= ticket.get('quantidade', 1)
                p['vendidos'] += ticket.get('quantidade', 1)
                break
        salvar_json(DATA_FILE, produtos)

        channel = bot.get_channel(int(canal_id))
        if channel:
            await atualizar_painel(channel)

        embed = discord.Embed(title="Compra Confirmada!", description="Ticket #" + str(ticket['id']) + " confirmado!", color=discord.Color.green())
        embed.set_thumbnail(url=IMG["correct"])
        embed.add_field(name="Cliente", value="<@" + str(ticket['user_id']) + ">", inline=True)
        embed.add_field(name="Produto", value=ticket['produto_nome'], inline=True)
        embed.add_field(name="Preco", value=ticket['produto_preco'], inline=True)
        embed.set_footer(text="Confirmado por: " + interaction.user.name, icon_url=IMG["double_check"])
        await interaction.response.send_message(embed=embed)

        vendas_channel = bot.get_channel(VENDAS_CANAL_ID)
        if vendas_channel:
            vendas_embed = discord.Embed(title="Venda Finalizada!", description="Nova venda confirmada!", color=0x820AD1)
            vendas_embed.set_author(name="New Store", icon_url=IMG["nubank"])
            vendas_embed.add_field(name="Usuario", value="`" + ticket['user_name'] + "`", inline=True)
            vendas_embed.add_field(name="Produto", value="`" + ticket['produto_nome'] + "`", inline=True)
            vendas_embed.add_field(name="Preco", value="`" + ticket['produto_preco'] + "`", inline=True)
            vendas_embed.add_field(name="Staff", value="`" + interaction.user.name + "`", inline=True)
            vendas_embed.add_field(name="Data", value="`" + discord.utils.utcnow().strftime('%d/%m/%Y %H:%M') + "`", inline=True)
            vendas_embed.set_footer(text="Vem Decolar, Vem com a New Store!", icon_url=IMG["nubank"])
            vendas_embed.set_image(url=IMG["banner"])
            await vendas_channel.send(embed=vendas_embed)

class EditarButton(Button):
    def __init__(self, prod_id, canal_id):
        super().__init__(label="Editar", emoji=E["editar"], style=discord.ButtonStyle.primary)
        self.prod_id = prod_id
        self.canal_id = canal_id
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EditarProdutoModal(self.prod_id, self.canal_id))

class ExcluirButton(Button):
    def __init__(self, prod_id, canal_id):
        super().__init__(label="Excluir", emoji=E["lixeira"], style=discord.ButtonStyle.danger)
        self.prod_id = prod_id
        self.canal_id = canal_id
    async def callback(self, interaction: discord.Interaction):
        produtos[self.canal_id] = [p for p in produtos.get(self.canal_id, []) if p['id'] != self.prod_id]
        salvar_json(DATA_FILE, produtos)
        channel = bot.get_channel(int(self.canal_id))
        if channel:
            await atualizar_painel(channel)
        embed = discord.Embed(title="Produto Excluido!", color=discord.Color.red())
        embed.set_image(url=IMG["delete"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoltarButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Voltar", emoji=E["voltar"], style=discord.ButtonStyle.secondary)
        self.canal_id = canal_id
    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ProdutoDropdown(self.canal_id, modo="editar"))
        await interaction.response.send_message("Selecione um produto:", view=view, ephemeral=True)

class AdicionarButton(Button):
    def __init__(self):
        super().__init__(label="Adicionar Produto", emoji=E["adicionar"], style=discord.ButtonStyle.success)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProdutoModal())

class ConfigPainelButton(Button):
    def __init__(self):
        super().__init__(label="Configurar Painel", emoji=E["logo"], style=discord.ButtonStyle.primary)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PainelModal())

class GerenciarButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Gerenciar Produtos", emoji=E["editar"], style=discord.ButtonStyle.secondary)
        self.canal_id = canal_id
    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ProdutoDropdown(self.canal_id, modo="editar"))
        await interaction.response.send_message("Selecione um produto:", view=view, ephemeral=True)

class ReporButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Repor Estoque", emoji=E["disponivel"], style=discord.ButtonStyle.success)
        self.canal_id = canal_id
    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ReporDropdown(self.canal_id))
        await interaction.response.send_message("Selecione o produto:", view=view, ephemeral=True)

class ReporDropdown(Select):
    def __init__(self, canal_id):
        self.canal_id = canal_id
        options = []
        for prod in produtos.get(canal_id, []):
            emoji = prod.get('emoji', E["produto"])
            options.append(discord.SelectOption(
                label=prod['nome'] + " - Estoque: " + str(prod['quantidade']),
                value=str(prod['id']),
                emoji=emoji
            ))
        if not options:
            options.append(discord.SelectOption(label="Sem produtos", value="none"))
        super().__init__(placeholder="Selecione para repor...", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            return
        prod_id = int(self.values[0])
        prod = next((p for p in produtos.get(self.canal_id, []) if p['id'] == prod_id), None)
        if prod:
            prod['quantidade'] += 1
            salvar_json(DATA_FILE, produtos)
            channel = bot.get_channel(int(self.canal_id))
            if channel:
                await atualizar_painel(channel)
            embed = discord.Embed(title="Estoque Reposto!", description="**" + prod['nome'] + "** agora tem " + str(prod['quantidade']) + " unidades!", color=discord.Color.green())
            embed.set_thumbnail(url=IMG["cardbox"])
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== DROPDOWN =====
class ProdutoDropdown(Select):
    def __init__(self, canal_id, modo="comprar"):
        self.canal_id = canal_id
        self.modo = modo
        options = []
        lista = produtos.get(canal_id, [])
        for prod in lista:
            # USA O EMOJI DO PRODUTO (novo) ou detecta automaticamente
            emoji_produto = prod.get('emoji', detectar_emoji_produto(prod['nome']))

            if prod['quantidade'] > 0 or modo == "editar":
                label = prod['nome'] + " - " + prod['preco']
                if prod['quantidade'] <= 3 and prod['quantidade'] > 0:
                    label += " [POUCO]"
                elif prod['quantidade'] == 0:
                    label += " [ESGOTADO]"
                options.append(discord.SelectOption(
                    label=label[:100],
                    description="Estoque: " + str(prod['quantidade']) + " | Vendidos: " + str(prod['vendidos']),
                    value=str(prod['id']),
                    emoji=emoji_produto  # AQUI ESTA O EMOJI DA MARCA!
                ))
        if not options:
            options.append(discord.SelectOption(
                label="Nenhum produto disponivel",
                description="Adicione produtos primeiro!",
                value="none",
                emoji=E["lixeira"]
            ))
        super().__init__(placeholder="Selecione um produto...", options=options[:25], min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nenhum produto disponivel!", ephemeral=True)
            return

        prod_id = int(self.values[0])
        prod = next((p for p in produtos.get(self.canal_id, []) if p['id'] == prod_id), None)
        if not prod:
            await interaction.response.send_message("Produto nao encontrado!", ephemeral=True)
            return

        if self.modo == "comprar":
            if prod['quantidade'] <= 0:
                embed = discord.Embed(title="Produto Esgotado!", color=discord.Color.red())
                embed.set_image(url=IMG["forbidden"])
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Cria canal de carrinho
            guild = interaction.guild
            categoria = guild.get_channel(CATEGORIA_CARRINHOS_ID)
            if not categoria:
                await interaction.response.send_message("Categoria de carrinhos nao encontrada!", ephemeral=True)
                return

            canal_nome = "carrinho-" + interaction.user.name.lower().replace(" ", "-")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            }
            # Adiciona permissao para staff
            staff_role = guild.get_role(STAFF_ROLE_ID)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

            novo_canal = await guild.create_text_channel(
                name=canal_nome,
                category=categoria,
                overwrites=overwrites
            )

            # Salva carrinho
            carrinho_id = str(novo_canal.id)
            carrinhos[carrinho_id] = {
                "user_id": interaction.user.id,
                "user_name": interaction.user.name,
                "produto_id": prod_id,
                "canal_id": self.canal_id,
                "quantidade_desejada": 1,
                "status": "aberto"
            }
            salvar_json(CARRINHOS_FILE, carrinhos)

            # Cria embed do carrinho
            embed = discord.Embed(
                title=E["carrinho"] + " **New Store | Vendas**",
                description="Carrinho de **" + interaction.user.mention + "**",
                color=0x820AD1
            )
            embed.add_field(
                name=E["produto"] + " **Produto |** " + prod['nome'],
                value="",
                inline=False
            )
            embed.add_field(
                name=E["valor"] + " **Valor |** `" + prod['preco'] + "`",
                value="",
                inline=False
            )
            embed.add_field(
                name=E["quantidade"] + " **Quantidade |** `" + str(carrinhos[carrinho_id]['quantidade_desejada']) + "`",
                value="",
                inline=False
            )
            embed.add_field(
                name=E["disponivel"] + " **Quantidade Disponivel |** `" + str(prod['quantidade']) + "`",
                value="",
                inline=False
            )
            embed.set_footer(text="Use os botoes abaixo para ajustar sua compra", icon_url=IMG["nubank"])

            view = View()
            view.add_item(MenosButton(carrinho_id))
            view.add_item(LapisButton(carrinho_id))
            view.add_item(MaisButton(carrinho_id))
            view.add_item(RemoverButton(carrinho_id))
            view.add_item(PagamentoButton(carrinho_id))
            view.add_item(ConfirmarCarrinhoButton(carrinho_id))

            await novo_canal.send(content=interaction.user.mention + " | " + (staff_role.mention if staff_role else "@Staff"), embed=embed, view=view)
            await interaction.response.send_message("Carrinho criado em " + novo_canal.mention + "!", ephemeral=True)

        elif self.modo == "editar":
            view = View()
            view.add_item(EditarButton(prod_id, self.canal_id))
            view.add_item(ExcluirButton(prod_id, self.canal_id))
            view.add_item(VoltarButton(self.canal_id))
            desc_text = "Preco: " + prod['preco'] + chr(10) + "Estoque: " + str(prod['quantidade']) + chr(10) + "Vendidos: " + str(prod['vendidos']) + chr(10) + "Emoji: " + prod.get('emoji', detectar_emoji_produto(prod['nome']))
            embed = discord.Embed(title="Editar: " + prod['nome'], description=desc_text, color=discord.Color.blue())
            embed.set_thumbnail(url=IMG["hammer"])
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ===== FUNCOES AUXILIARES =====
async def atualizar_embed_carrinho(canal, carrinho):
    prod = next((p for p in produtos.get(carrinho['canal_id'], []) if p['id'] == carrinho['produto_id']), None)
    if not prod:
        return

    embed = discord.Embed(
        title=E["carrinho"] + " **New Store | Vendas**",
        description="Carrinho de **<@" + str(carrinho['user_id']) + ">**",
        color=0x820AD1
    )
    embed.add_field(
        name=E["produto"] + " **Produto |** " + prod['nome'],
        value="",
        inline=False
    )
    embed.add_field(
        name=E["valor"] + " **Valor |** `" + prod['preco'] + "`",
        value="",
        inline=False
    )
    embed.add_field(
        name=E["quantidade"] + " **Quantidade |** `" + str(carrinho['quantidade_desejada']) + "`",
        value="",
        inline=False
    )
    embed.add_field(
        name=E["disponivel"] + " **Quantidade Disponivel |** `" + str(prod['quantidade']) + "`",
        value="",
        inline=False
    )
    embed.set_footer(text="Use os botoes abaixo para ajustar sua compra", icon_url=IMG["nubank"])

    view = View()
    view.add_item(MenosButton(str(canal.id)))
    view.add_item(LapisButton(str(canal.id)))
    view.add_item(MaisButton(str(canal.id)))
    view.add_item(RemoverButton(str(canal.id)))
    view.add_item(PagamentoButton(str(canal.id)))
    view.add_item(ConfirmarCarrinhoButton(str(canal.id)))

    async for msg in canal.history(limit=10):
        if msg.author == bot.user and msg.embeds and "New Store | Vendas" in msg.embeds[0].title:
            await msg.edit(embed=embed, view=view)
            return

async def atualizar_painel(channel):
    canal_id = str(channel.id)
    config = paineis.get(canal_id)
    if not config:
        return

    lista = produtos.get(canal_id, [])
    total_produtos = len(lista)
    total_estoque = sum(p['quantidade'] for p in lista)
    total_vendidos = sum(p['vendidos'] for p in lista)

    desc = "> " + config['descricao'] + chr(10) + chr(10) + "`━━━━━━━━━━━━━━━━━━━━━━`"
    embed = discord.Embed(title="**" + config['titulo'] + "**", description=desc, color=config['cor'])
    embed.set_author(name="New Store", icon_url=IMG["nubank"])

    if lista:
        for prod in lista[:10]:
            emoji_produto = prod.get('emoji', detectar_emoji_produto(prod['nome']))
            status = "`" + E["disponivel"] + " Disponivel`" if prod['quantidade'] > 0 else "`" + E["lixeira"] + " Esgotado`"
            if prod['quantidade'] > 0 and prod['quantidade'] <= 3:
                status = "`" + E["status"] + " Poucas unidades!`"
            valor = E["preco"] + " `" + prod['preco'] + "` | " + E["produto"] + " `" + str(prod['quantidade']) + "` em estoque | " + status
            embed.add_field(name="`" + str(prod['id']) + "` " + emoji_produto + " **" + prod['nome'] + "** (" + prod['categoria'] + ")", value=valor, inline=False)
    else:
        embed.add_field(name=E["lixeira"] + " `Sem produtos`", value="Nenhum produto cadastrado. Use `/adicionar`!", inline=False)

    embed.add_field(name="`━━━━━━━━━━━━━━━━━━━━━━`", value=E["logo"] + " **Resumo**" + chr(10) + E["produto"] + " Produtos: `" + str(total_produtos) + "` | " + E["produto"] + " Estoque: `" + str(total_estoque) + "` | " + E["confirmar"] + " Vendidos: `" + str(total_vendidos) + "`", inline=False)

    if config.get('imagem'):
        embed.set_image(url=config['imagem'])
    if config.get('footer'):
        embed.set_footer(text=config['footer'], icon_url=IMG["nubank"])
    else:
        embed.set_footer(text="Clique no menu abaixo para comprar", icon_url=IMG["nubank"])

    async for msg in channel.history(limit=50):
        if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "**" + config['titulo'] + "**":
            view = View()
            view.add_item(ProdutoDropdown(canal_id, modo="comprar"))
            await msg.edit(embed=embed, view=view)
            return

# ===== COMANDOS SLASH =====
@bot.tree.command(name="adicionar", description="Adiciona um novo produto neste canal")
@app_commands.checks.has_permissions(administrator=True)
async def adicionar(interaction: discord.Interaction):
    await interaction.response.send_modal(ProdutoModal())

@bot.tree.command(name="painel", description="Envia/atualiza o painel de vendas deste canal")
@app_commands.checks.has_permissions(administrator=True)
async def painel(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    config = paineis.get(canal_id)
    if not config:
        embed = discord.Embed(title="Painel nao configurado!", description="Use /configurar primeiro.", color=discord.Color.red())
        embed.set_image(url=IMG["forbidden"])
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    lista = produtos.get(canal_id, [])
    total_produtos = len(lista)
    total_estoque = sum(p['quantidade'] for p in lista)
    total_vendidos = sum(p['vendidos'] for p in lista)

    desc = "> " + config['descricao'] + chr(10) + chr(10) + "`━━━━━━━━━━━━━━━━━━━━━━`"
    embed = discord.Embed(title="**" + config['titulo'] + "**", description=desc, color=config['cor'])
    embed.set_author(name="New Store", icon_url=IMG["nubank"])

    if lista:
        for prod in lista[:10]:
            emoji_produto = prod.get('emoji', detectar_emoji_produto(prod['nome']))
            status = "`" + E["disponivel"] + " Disponivel`" if prod['quantidade'] > 0 else "`" + E["lixeira"] + " Esgotado`"
            if prod['quantidade'] > 0 and prod['quantidade'] <= 3:
                status = "`" + E["status"] + " Poucas unidades!`"
            valor = E["preco"] + " `" + prod['preco'] + "` | " + E["produto"] + " `" + str(prod['quantidade']) + "` em estoque | " + status
            embed.add_field(name="`" + str(prod['id']) + "` " + emoji_produto + " **" + prod['nome'] + "** (" + prod['categoria'] + ")", value=valor, inline=False)
    else:
        embed.add_field(name=E["lixeira"] + " `Sem produtos`", value="Nenhum produto cadastrado. Use `/adicionar`!", inline=False)

    embed.add_field(name="`━━━━━━━━━━━━━━━━━━━━━━`", value=E["logo"] + " **Resumo**" + chr(10) + E["produto"] + " Produtos: `" + str(total_produtos) + "` | " + E["produto"] + " Estoque: `" + str(total_estoque) + "` | " + E["confirmar"] + " Vendidos: `" + str(total_vendidos) + "`", inline=False)

    if config.get('imagem'):
        embed.set_image(url=config['imagem'])
    if config.get('footer'):
        embed.set_footer(text=config['footer'], icon_url=IMG["nubank"])
    else:
        embed.set_footer(text="Clique no menu abaixo para comprar", icon_url=IMG["nubank"])

    view = View()
    view.add_item(ProdutoDropdown(canal_id, modo="comprar"))
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="configurar", description="Configura o painel deste canal")
@app_commands.checks.has_permissions(administrator=True)
async def configurar(interaction: discord.Interaction):
    await interaction.response.send_modal(PainelModal())

@bot.tree.command(name="gerenciar", description="Gerencia produtos deste canal")
@app_commands.checks.has_permissions(administrator=True)
async def gerenciar(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    view = View()
    view.add_item(ProdutoDropdown(canal_id, modo="editar"))
    view.add_item(VoltarButton(canal_id))
    await interaction.response.send_message("Selecione um produto:", view=view, ephemeral=True)

@bot.tree.command(name="repor", description="Repor estoque de um produto")
@app_commands.checks.has_permissions(administrator=True)
async def repor(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    view = View()
    view.add_item(ReporDropdown(canal_id))
    await interaction.response.send_message("Selecione o produto:", view=view, ephemeral=True)

@bot.tree.command(name="estoque", description="Ver estoque completo deste canal")
async def estoque(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    lista = produtos.get(canal_id, [])
    if not lista:
        embed = discord.Embed(title="Nenhum produto!", color=discord.Color.red())
        embed.set_image(url=IMG["forbidden"])
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    embed = discord.Embed(title="Estoque", description="Canal: " + interaction.channel.name, color=discord.Color.blue())
    embed.set_thumbnail(url=IMG["cardbox"])
    for prod in lista:
        emoji = prod.get('emoji', detectar_emoji_produto(prod['nome']))
        embed.add_field(name=emoji + " " + prod['nome'], value=prod['preco'] + " | Estoque: " + str(prod['quantidade']) + " | Vendidos: " + str(prod['vendidos']), inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="admin", description="Painel de administracao completo")
@app_commands.checks.has_permissions(administrator=True)
async def admin(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    embed = discord.Embed(title="Painel de Administracao", description="Gerencie seus produtos", color=discord.Color.purple())
    embed.set_thumbnail(url=IMG["hammer"])
    embed.add_field(name="Produtos", value=str(len(produtos.get(canal_id, []))), inline=True)
    embed.add_field(name="Total Estoque", value=str(sum(p['quantidade'] for p in produtos.get(canal_id, []))), inline=True)
    embed.add_field(name="Total Vendidos", value=str(sum(p['vendidos'] for p in produtos.get(canal_id, []))), inline=True)
    view = View()
    view.add_item(AdicionarButton())
    view.add_item(ConfigPainelButton())
    view.add_item(GerenciarButton(canal_id))
    view.add_item(ReporButton(canal_id))
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="resetar", description="Apaga TODOS os produtos deste canal")
@app_commands.checks.has_permissions(administrator=True)
async def resetar(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)
    if canal_id in produtos:
        qtd = len(produtos[canal_id])
        produtos[canal_id] = []
        salvar_json(DATA_FILE, produtos)
        await atualizar_painel(interaction.channel)
        embed = discord.Embed(title="Produtos Apagados!", description=str(qtd) + " produtos removidos.", color=discord.Color.red())
        embed.set_image(url=IMG["delete"])
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("Nenhum produto.", ephemeral=True)

# ===== EVENTOS =====
@bot.event
async def on_ready():
    print("Bot ligado como " + str(bot.user))
    print(str(len(produtos)) + " canais com produtos")
    print(str(len(paineis)) + " canais com painel configurado")
    print(str(len(tickets)) + " tickets criados")
    print(str(len(carrinhos)) + " carrinhos ativos")
    try:
        synced = await bot.tree.sync()
        print(str(len(synced)) + " comandos sincronizados")
    except Exception as e:
        print("Erro ao sincronizar: " + str(e))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Sem permissao!")
    else:
        print("Erro: " + str(error))

# ===== INICIAR =====
if __name__ == "__main__":
    if not TOKEN:
        print("ERRO: DISCORD_TOKEN nao encontrado no .env!")
        print("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
    else:
        bot.run(TOKEN)
