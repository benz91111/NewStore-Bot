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

# IDs fixos
STAFF_ROLE_ID = 1512273191152783410
VENDAS_CANAL_ID = 1512216907863036125

# ===== IMAGENS DO IMGUR =====
IMG = {
    "logo": "https://i.imgur.com/ljygZWH.png",
    "cart": "https://i.imgur.com/uNzcFQG.png",
    "card": "https://i.imgur.com/gFauOje.png",
    "gift": "https://i.imgur.com/PbjEZX2.png",
    "dollar": "https://i.imgur.com/5sdf0Ng.png",
    "clock": "https://i.imgur.com/7HNO9g8.png",
    "correct": "https://i.imgur.com/iBQmtbf.png",
    "double_check": "https://i.imgur.com/3mQVp90.png",
    "delete": "https://i.imgur.com/U10LD6r.png",
    "like": "https://i.imgur.com/tBUACfu.png",
    "deslike": "https://i.imgur.com/1bOAMp9.gif",
    "forbidden": "https://i.imgur.com/GH72rDY.png",
    "group": "https://i.imgur.com/P5ZjUIy.png",
    "hammer": "https://i.imgur.com/2h5uqCc.png",
    "donation": "https://i.imgur.com/47IRZjt.png",
    "donation2": "https://i.imgur.com/1MjK13V.png",
    "dir": "https://i.imgur.com/puw8Xjc.png",
    "cardbox": "https://i.imgur.com/b9yyfwZ.png",
    "nubank": "https://i.imgur.com/z7OYi2n.png",
    "less18": "https://i.imgur.com/8GUnzM0.png",
    "dnd": "https://i.imgur.com/955eTnK.png",
    "banner": "https://i.imgur.com/jDo23VT.png",
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

# ===== BOT =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== MODAIS =====
class ProdutoModal(Modal, title="Adicionar Produto"):
    nome = TextInput(
        label="Nome do produto",
        placeholder="Ex: Netflix Premium",
        max_length=50
    )
    descricao = TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Descricao do produto...",
        max_length=400
    )
    preco = TextInput(
        label="Preco",
        placeholder="Ex: R$ 15,00 ou 15.00",
        max_length=20
    )
    quantidade = TextInput(
        label="Quantidade em estoque",
        placeholder="Ex: 10",
        max_length=10
    )
    categoria = TextInput(
        label="Categoria (opcional)",
        placeholder="Ex: Contas, Gift Cards",
        required=False,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value.strip())
            if qtd < 0:
                await interaction.response.send_message(
                    "Quantidade nao pode ser negativa!", ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Quantidade precisa ser um numero inteiro!", ephemeral=True
            )
            return

        canal_id = str(interaction.channel_id)
        if canal_id not in produtos:
            produtos[canal_id] = []

        produto_id = len(produtos[canal_id]) + 1
        produto = {
            "id": produto_id,
            "nome": self.nome.value.strip(),
            "descricao": self.descricao.value.strip(),
            "preco": self.preco.value.strip(),
            "quantidade": qtd,
            "categoria": self.categoria.value.strip() if self.categoria.value else "Geral",
            "vendidos": 0
        }
        produtos[canal_id].append(produto)
        salvar_json(DATA_FILE, produtos)

        # Atualiza painel automaticamente
        await atualizar_painel(interaction.channel)

        embed = discord.Embed(
            title="Produto Adicionado!",
            description="**" + produto['nome'] + "** foi adicionado com sucesso!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=IMG["correct"])
        embed.add_field(name="Preco", value=produto['preco'], inline=True)
        embed.add_field(name="Estoque", value=str(produto['quantidade']), inline=True)
        embed.add_field(name="Categoria", value=produto['categoria'], inline=True)
        embed.set_footer(
            text="ID: " + str(produto_id) + " | Canal: " + interaction.channel.name,
            icon_url=IMG["cart"]
        )

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

    nome = TextInput(label="Nome", max_length=50)
    descricao = TextInput(label="Descricao", style=discord.TextStyle.paragraph, max_length=400)
    preco = TextInput(label="Preco", max_length=20)
    quantidade = TextInput(label="Quantidade", max_length=10)
    categoria = TextInput(label="Categoria", required=False, max_length=30)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade.value.strip())
            if qtd < 0:
                await interaction.response.send_message(
                    "Quantidade nao pode ser negativa!", ephemeral=True
                )
                return
        except ValueError:
            await interaction.response.send_message(
                "Quantidade precisa ser um numero inteiro!", ephemeral=True
            )
            return

        for p in produtos.get(self.canal_id, []):
            if p['id'] == self.produto_id:
                p['nome'] = self.nome.value.strip()
                p['descricao'] = self.descricao.value.strip()
                p['preco'] = self.preco.value.strip()
                p['quantidade'] = qtd
                p['categoria'] = self.categoria.value.strip() if self.categoria.value else "Geral"
                break
        salvar_json(DATA_FILE, produtos)

        # Atualiza painel automaticamente
        channel = bot.get_channel(int(self.canal_id))
        if channel:
            await atualizar_painel(channel)

        await interaction.response.send_message(
            "Produto editado com sucesso!", ephemeral=True
        )

class PainelModal(Modal, title="Configurar Painel"):
    titulo = TextInput(
        label="Titulo do painel",
        placeholder="Ex: Loja de Contas",
        max_length=100
    )
    descricao = TextInput(
        label="Descricao",
        style=discord.TextStyle.paragraph,
        placeholder="Bem-vindo a nossa loja...",
        max_length=500
    )
    cor = TextInput(
        label="Cor (hex)",
        placeholder="Ex: #820AD1 ou deixe em branco",
        required=False,
        max_length=7
    )
    imagem = TextInput(
        label="URL da imagem (opcional)",
        placeholder="https://...",
        required=False,
        max_length=200
    )
    footer = TextInput(
        label="Rodape (opcional)",
        placeholder="Ex: Clique abaixo para comprar",
        required=False,
        max_length=100
    )

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
        await interaction.response.send_message(
            "Painel configurado! Use /painel para enviar.", ephemeral=True
        )

# ===== VIEWS E BOTOES =====
class ProdutoDropdown(Select):
    def __init__(self, canal_id, modo="comprar"):
        self.canal_id = canal_id
        self.modo = modo
        options = []
        lista = produtos.get(canal_id, [])

        for prod in lista:
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
                    emoji="🛒" if prod['quantidade'] > 0 else "❌"
                ))

        if not options:
            options.append(discord.SelectOption(
                label="Nenhum produto disponivel",
                description="Adicione produtos primeiro!",
                value="none",
                emoji="❌"
            ))

        super().__init__(
            placeholder="Selecione um produto...",
            options=options[:25],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("Nenhum produto disponivel!", ephemeral=True)
            return

        prod_id = int(self.values[0])
        prod = next((p for p in produtos.get(self.canal_id, []) if p['id'] == prod_id), None)

        if not prod:
            await interaction.response.send_message(
                "Produto nao encontrado!", ephemeral=True
            )
            return

        if self.modo == "comprar":
            if prod['quantidade'] <= 0:
                embed = discord.Embed(
                    title="Produto Esgotado!",
                    color=discord.Color.red()
                )
                embed.set_image(url=IMG["forbidden"])
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Cria ticket de venda
            ticket_id = len(tickets) + 1
            ticket = {
                "id": ticket_id,
                "user_id": interaction.user.id,
                "user_name": interaction.user.name,
                "produto_id": prod_id,
                "produto_nome": prod['nome'],
                "produto_preco": prod['preco'],
                "quantidade": 1,
                "status": "pendente",
                "canal_id": interaction.channel_id,
                "timestamp": str(discord.utils.utcnow())
            }
            tickets.append(ticket)
            salvar_json(TICKETS_FILE, tickets)

            # Cria embed do ticket
            embed = discord.Embed(
                title="Ticket de Venda #" + str(ticket_id),
                description="Nova compra iniciada!",
                color=0x820AD1
            )
            embed.set_thumbnail(url=IMG["nubank"])
            embed.add_field(
                name="Usuario",
                value=interaction.user.mention + " (" + interaction.user.name + ")",
                inline=False
            )
            embed.add_field(
                name="Produto",
                value="**" + prod['nome'] + "**",
                inline=True
            )
            embed.add_field(
                name="Preco",
                value=prod['preco'],
                inline=True
            )
            embed.add_field(
                name="Descricao",
                value=prod['descricao'],
                inline=False
            )
            embed.add_field(
                name="Status",
                value="Aguardando confirmacao da Staff",
                inline=False
            )
            embed.set_footer(
                text="ID: " + str(ticket_id) + " | Aguarde a Staff confirmar",
                icon_url=IMG["cart"]
            )

            # Mencao ao cargo Staff
            guild = interaction.guild
            staff_role = guild.get_role(STAFF_ROLE_ID)
            staff_mention = staff_role.mention if staff_role else "@Staff"

            view = View()
            view.add_item(ConfirmarCompraButton(ticket_id))

            msg_text = interaction.user.mention + " iniciou uma compra!\n" + staff_mention + " aguarde confirmacao."
            await interaction.response.send_message(
                msg_text,
                embed=embed,
                view=view
            )

        elif self.modo == "editar":
            view = View()
            view.add_item(EditarButton(prod_id, self.canal_id))
            view.add_item(ExcluirButton(prod_id, self.canal_id))
            view.add_item(VoltarButton(self.canal_id))

            desc_text = "Preco: " + prod['preco'] + "\nEstoque: " + str(prod['quantidade']) + "\nVendidos: " + str(prod['vendidos'])
            embed = discord.Embed(
                title="Editar: " + prod['nome'],
                description=desc_text,
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=IMG["hammer"])
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmarCompraButton(Button):
    def __init__(self, ticket_id):
        super().__init__(
            label="Confirmar Compra",
            style=discord.ButtonStyle.success,
            emoji="✅"
        )
        self.ticket_id = ticket_id

    async def callback(self, interaction: discord.Interaction):
        # Verifica se eh staff
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "Apenas Staff pode confirmar compras!", ephemeral=True
            )
            return

        # Busca ticket
        ticket = next((t for t in tickets if t['id'] == self.ticket_id), None)
        if not ticket:
            await interaction.response.send_message(
                "Ticket nao encontrado!", ephemeral=True
            )
            return

        if ticket['status'] == "confirmado":
            await interaction.response.send_message(
                "Esta compra ja foi confirmada!", ephemeral=True
            )
            return

        # Atualiza ticket
        ticket['status'] = "confirmado"
        ticket['staff_id'] = interaction.user.id
        ticket['staff_name'] = interaction.user.name
        salvar_json(TICKETS_FILE, tickets)

        # Diminui estoque
        canal_id = str(ticket['canal_id'])
        for p in produtos.get(canal_id, []):
            if p['id'] == ticket['produto_id']:
                p['quantidade'] -= 1
                p['vendidos'] += 1
                break
        salvar_json(DATA_FILE, produtos)

        # Atualiza painel
        channel = bot.get_channel(int(canal_id))
        if channel:
            await atualizar_painel(channel)

        # Embed de confirmacao
        embed = discord.Embed(
            title="Compra Confirmada!",
            description="Ticket #" + str(ticket['id']) + " confirmado por " + interaction.user.mention,
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=IMG["correct"])
        embed.add_field(
            name="Cliente",
            value="<@" + str(ticket['user_id']) + "> (" + ticket['user_name'] + ")",
            inline=True
        )
        embed.add_field(
            name="Produto",
            value=ticket['produto_nome'],
            inline=True
        )
        embed.add_field(
            name="Preco",
            value=ticket['produto_preco'],
            inline=True
        )
        embed.set_footer(
            text="Confirmado por: " + interaction.user.name,
            icon_url=IMG["double_check"]
        )

        await interaction.response.send_message(embed=embed)

        # Envia para canal de vendas finalizadas
        vendas_channel = bot.get_channel(VENDAS_CANAL_ID)
        if vendas_channel:
            vendas_embed = discord.Embed(
                title="Venda Finalizada!",
                description="Nova venda confirmada!",
                color=0x820AD1
            )
            vendas_embed.set_author(
                name="New Store",
                icon_url=IMG["nubank"]
            )
            vendas_embed.add_field(
                name="Usuario",
                value="`" + ticket['user_name'] + "`",
                inline=True
            )
            vendas_embed.add_field(
                name="Produto",
                value="`" + ticket['produto_nome'] + "`",
                inline=True
            )
            vendas_embed.add_field(
                name="Preco",
                value="`" + ticket['produto_preco'] + "`",
                inline=True
            )
            vendas_embed.add_field(
                name="Staff",
                value="`" + interaction.user.name + "`",
                inline=True
            )
            vendas_embed.add_field(
                name="Data",
                value="`" + discord.utils.utcnow().strftime('%d/%m/%Y %H:%M') + "`",
                inline=True
            )
            vendas_embed.set_footer(
                text="Vem Decolar, Vem com a New Store!",
                icon_url=IMG["nubank"]
            )
            vendas_embed.set_image(url=IMG["banner"])

            await vendas_channel.send(embed=vendas_embed)

class EditarButton(Button):
    def __init__(self, prod_id, canal_id):
        super().__init__(label="Editar", style=discord.ButtonStyle.primary, emoji="✏")
        self.prod_id = prod_id
        self.canal_id = canal_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EditarProdutoModal(self.prod_id, self.canal_id))

class ExcluirButton(Button):
    def __init__(self, prod_id, canal_id):
        super().__init__(label="Excluir", style=discord.ButtonStyle.danger, emoji="🗑")
        self.prod_id = prod_id
        self.canal_id = canal_id

    async def callback(self, interaction: discord.Interaction):
        produtos[self.canal_id] = [p for p in produtos.get(self.canal_id, []) if p['id'] != self.prod_id]
        salvar_json(DATA_FILE, produtos)

        # Atualiza painel
        channel = bot.get_channel(int(self.canal_id))
        if channel:
            await atualizar_painel(channel)

        embed = discord.Embed(title="Produto Excluido!", color=discord.Color.red())
        embed.set_image(url=IMG["delete"])
        await interaction.response.send_message(embed=embed, ephemeral=True)

class VoltarButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Voltar", style=discord.ButtonStyle.secondary, emoji="⬅")
        self.canal_id = canal_id

    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ProdutoDropdown(self.canal_id, modo="editar"))
        await interaction.response.send_message("Selecione um produto:", view=view, ephemeral=True)

class AdicionarButton(Button):
    def __init__(self):
        super().__init__(label="Adicionar Produto", style=discord.ButtonStyle.success, emoji="➕")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ProdutoModal())

class ConfigPainelButton(Button):
    def __init__(self):
        super().__init__(label="Configurar Painel", style=discord.ButtonStyle.primary, emoji="⚙")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PainelModal())

class GerenciarButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Gerenciar Produtos", style=discord.ButtonStyle.secondary, emoji="🔨")
        self.canal_id = canal_id

    async def callback(self, interaction: discord.Interaction):
        view = View()
        view.add_item(ProdutoDropdown(self.canal_id, modo="editar"))
        await interaction.response.send_message("Selecione um produto:", view=view, ephemeral=True)

class ReporButton(Button):
    def __init__(self, canal_id):
        super().__init__(label="Repor Estoque", style=discord.ButtonStyle.success, emoji="📦")
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
            options.append(discord.SelectOption(
                label=prod['nome'] + " - Estoque: " + str(prod['quantidade']),
                value=str(prod['id']),
                emoji="📦"
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

            # Atualiza painel
            channel = bot.get_channel(int(self.canal_id))
            if channel:
                await atualizar_painel(channel)

            embed = discord.Embed(
                title="Estoque Reposto!",
                description="**" + prod['nome'] + "** agora tem " + str(prod['quantidade']) + " unidades!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=IMG["cardbox"])
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== FUNCAO AUXILIAR: ATUALIZAR PAINEL =====
async def atualizar_painel(channel):
    canal_id = str(channel.id)
    config = paineis.get(canal_id)
    if not config:
        return

    lista = produtos.get(canal_id, [])
    total_produtos = len(lista)
    total_estoque = sum(p['quantidade'] for p in lista)
    total_vendidos = sum(p['vendidos'] for p in lista)

    embed = discord.Embed(
        title=config['titulo'],
        description=config['descricao'],
        color=config['cor']
    )
    embed.set_author(name="New Store", icon_url=IMG["nubank"])

    if lista:
        for prod in lista[:10]:
            status = "Disponivel" if prod['quantidade'] > 0 else "Esgotado"
            if prod['quantidade'] > 0 and prod['quantidade'] <= 3:
                status = "Poucas unidades!"

            valor = prod['preco'] + " | Estoque: " + str(prod['quantidade']) + " | " + status
            embed.add_field(
                name=str(prod['id']) + ". " + prod['nome'] + " (" + prod['categoria'] + ")",
                value=valor,
                inline=False
            )
    else:
        embed.add_field(name="---", value="Nenhum produto cadastrado ainda.", inline=False)

    embed.add_field(
        name="Resumo",
        value="Produtos: " + str(total_produtos) + " | Estoque: " + str(total_estoque) + " | Vendidos: " + str(total_vendidos),
        inline=False
    )

    if config.get('imagem'):
        embed.set_image(url=config['imagem'])
    if config.get('footer'):
        embed.set_footer(text=config['footer'], icon_url=IMG["cart"])
    else:
        embed.set_footer(text="Clique no menu abaixo para comprar", icon_url=IMG["cart"])

    # Procura mensagem do bot para editar
    async for msg in channel.history(limit=50):
        if msg.author == bot.user and msg.embeds and msg.embeds[0].title == config['titulo']:
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
        embed = discord.Embed(
            title="Painel nao configurado!",
            description="Use /configurar primeiro para definir o painel deste canal.",
            color=discord.Color.red()
        )
        embed.set_image(url=IMG["forbidden"])
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    lista = produtos.get(canal_id, [])
    total_produtos = len(lista)
    total_estoque = sum(p['quantidade'] for p in lista)
    total_vendidos = sum(p['vendidos'] for p in lista)

    embed = discord.Embed(
        title=config['titulo'],
        description=config['descricao'],
        color=config['cor']
    )
    embed.set_author(name="New Store", icon_url=IMG["nubank"])

    if lista:
        for prod in lista[:10]:
            status = "Disponivel" if prod['quantidade'] > 0 else "Esgotado"
            if prod['quantidade'] > 0 and prod['quantidade'] <= 3:
                status = "Poucas unidades!"

            valor = prod['preco'] + " | Estoque: " + str(prod['quantidade']) + " | " + status
            embed.add_field(
                name=str(prod['id']) + ". " + prod['nome'] + " (" + prod['categoria'] + ")",
                value=valor,
                inline=False
            )
    else:
        embed.add_field(name="---", value="Nenhum produto cadastrado ainda.", inline=False)

    embed.add_field(
        name="Resumo",
        value="Produtos: " + str(total_produtos) + " | Estoque: " + str(total_estoque) + " | Vendidos: " + str(total_vendidos),
        inline=False
    )

    if config.get('imagem'):
        embed.set_image(url=config['imagem'])
    if config.get('footer'):
        embed.set_footer(text=config['footer'], icon_url=IMG["cart"])
    else:
        embed.set_footer(text="Clique no menu abaixo para comprar", icon_url=IMG["cart"])

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

    embed = discord.Embed(
        title="Estoque",
        description="Canal: " + interaction.channel.name,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=IMG["cardbox"])

    for prod in lista:
        embed.add_field(
            name=prod['nome'],
            value=prod['preco'] + " | Estoque: " + str(prod['quantidade']) + " | Vendidos: " + str(prod['vendidos']),
            inline=True
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="admin", description="Painel de administracao completo")
@app_commands.checks.has_permissions(administrator=True)
async def admin(interaction: discord.Interaction):
    canal_id = str(interaction.channel_id)

    embed = discord.Embed(
        title="Painel de Administracao",
        description="Gerencie seus produtos e painel",
        color=discord.Color.purple()
    )
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

        # Atualiza painel
        await atualizar_painel(interaction.channel)

        embed = discord.Embed(
            title="Produtos Apagados!",
            description=str(qtd) + " produtos removidos.",
            color=discord.Color.red()
        )
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
