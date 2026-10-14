"""Interface da batalha em pygame (seção 5.8 do guia).

Mostra a arena, a energia de cada robô, os tiros do último tick, o vencedor e,
ao lado, o painel do compilador de cada participante: as 6 etapas com o seu
status e, se houve erro, a linha e o motivo.

Controles: espaço pausa, setas para cima/baixo mudam a velocidade, Esc sai.
"""
from typing import List

import pygame

from ..compiler.pipeline import ERRO, OK
from .arena import MAX_TICKS, TAMANHO, Arena, Participante, texto_resultado

LADO_ARENA = 700  # pixels da arena na tela
LARGURA_PAINEL = 380
ESCALA = LADO_ARENA / TAMANHO
RAIO_ROBO = 12
FPS = 30
MAX_TICKS_POR_QUADRO = 64

FUNDO = (24, 26, 33)
FUNDO_PAINEL = (34, 37, 46)
BORDA = (80, 84, 96)
TEXTO = (225, 228, 235)
APAGADO = (120, 124, 135)
VERDE = (80, 200, 120)
VERMELHO = (230, 80, 80)
CORES_ROBOS = [(80, 160, 255), (255, 170, 60), (190, 110, 255),
               (60, 210, 200), (255, 110, 170), (200, 210, 80)]
COR_ETAPA = {OK: VERDE, ERRO: VERMELHO}  # pendente e pulada ficam apagadas


def para_tela(x: float, y: float) -> tuple:
    return int(x * ESCALA), int(y * ESCALA)


def quebrar_texto(texto: str, fonte, largura: int) -> List[str]:
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if atual and fonte.size(tentativa)[0] > largura:
            linhas.append(atual)
            tentativa = palavra
        atual = tentativa
    return linhas + [atual] if atual else linhas


class Interface:
    def __init__(self, arena: Arena, participantes: List[Participante]):
        self.arena = arena
        self.participantes = participantes
        self.cores = {id(p.robo): CORES_ROBOS[i % len(CORES_ROBOS)]
                      for i, p in enumerate(participantes) if p.robo is not None}
        self.ticks_por_quadro = 1
        self.pausado = False
        pygame.init()
        pygame.display.set_caption("Compiler Arena")
        self.tela = pygame.display.set_mode((LADO_ARENA + LARGURA_PAINEL, LADO_ARENA))
        self.fonte = pygame.font.SysFont("arial", 14)
        self.fonte_titulo = pygame.font.SysFont("arial", 16, bold=True)
        self.fonte_grande = pygame.font.SysFont("arial", 32, bold=True)

    def rodar(self):
        relogio = pygame.time.Clock()
        while self._tratar_eventos():
            if not self.pausado:
                for _ in range(self.ticks_por_quadro):
                    self.arena.executar_tick()
            self.desenhar()
            pygame.display.flip()
            relogio.tick(FPS)
        pygame.quit()
        return self.arena.vencedor

    def _tratar_eventos(self) -> bool:
        """Devolve False quando o usuário fecha a janela."""
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    return False
                if evento.key == pygame.K_SPACE:
                    self.pausado = not self.pausado
                elif evento.key == pygame.K_UP:
                    self.ticks_por_quadro = min(MAX_TICKS_POR_QUADRO, self.ticks_por_quadro * 2)
                elif evento.key == pygame.K_DOWN:
                    self.ticks_por_quadro = max(1, self.ticks_por_quadro // 2)
        return True

    def desenhar(self) -> None:
        self.tela.fill(FUNDO)
        pygame.draw.rect(self.tela, BORDA, (0, 0, LADO_ARENA, LADO_ARENA), 2)
        for tiro in self.arena.tiros:
            self._desenhar_tiro(tiro)
        for robo in self.arena.robos:
            self._desenhar_robo(robo)
        self._desenhar_painel()
        if self.arena.terminou:
            self._desenhar_resultado()

    def _texto(self, texto: str, posicao: tuple, cor=TEXTO, fonte=None, centro=False) -> None:
        imagem = (fonte or self.fonte).render(texto, True, cor)
        retangulo = imagem.get_rect(center=posicao) if centro else imagem.get_rect(topleft=posicao)
        self.tela.blit(imagem, retangulo)

    def _desenhar_tiro(self, tiro) -> None:
        inicio = para_tela(tiro.atirador.x, tiro.atirador.y)
        fim = para_tela(tiro.x_fim, tiro.y_fim)
        pygame.draw.line(self.tela, self.cores[id(tiro.atirador)], inicio, fim, 2)
        if tiro.alvo is not None:
            pygame.draw.circle(self.tela, VERMELHO, fim, RAIO_ROBO + 4, 2)

    def _desenhar_robo(self, robo) -> None:
        cx, cy = para_tela(robo.x, robo.y)
        if not robo.vivo:
            pygame.draw.circle(self.tela, APAGADO, (cx, cy), RAIO_ROBO, 2)
            self._texto("X", (cx, cy), APAGADO, centro=True)
            return
        cor = self.cores[id(robo)]
        pygame.draw.circle(self.tela, cor, (cx, cy), RAIO_ROBO)
        frente = pygame.math.Vector2(RAIO_ROBO + 8, 0).rotate(robo.direcao)
        pygame.draw.line(self.tela, TEXTO, (cx, cy), (cx + frente.x, cy + frente.y), 3)
        self._texto(robo.nome, (cx, cy - RAIO_ROBO - 12), cor, centro=True)
        barra = (cx - 20, cy + RAIO_ROBO + 6, 40, 5)
        pygame.draw.rect(self.tela, BORDA, barra)
        pygame.draw.rect(self.tela, VERDE, (barra[0], barra[1], 40 * robo.energia // 100, 5))

    def _desenhar_painel(self) -> None:
        x0 = LADO_ARENA
        pygame.draw.rect(self.tela, FUNDO_PAINEL, (x0, 0, LARGURA_PAINEL, LADO_ARENA))
        x, y = x0 + 16, 14
        largura = LARGURA_PAINEL - 32
        for participante in self.participantes:
            y = self._desenhar_participante(participante, x, y, largura) + 14
        estado = "PAUSADO" if self.pausado else f"velocidade {self.ticks_por_quadro}x"
        self._texto(f"Tick {self.arena.tick}/{MAX_TICKS}   {estado}",
                    (x, LADO_ARENA - 44), APAGADO)
        self._texto("Espaço: pausa   setas: velocidade   Esc: sair",
                    (x, LADO_ARENA - 24), APAGADO)

    def _desenhar_participante(self, participante: Participante, x: int, y: int, largura: int) -> int:
        """Desenha o painel de um robô e devolve o y logo abaixo dele."""
        resultado, robo = participante
        ast = resultado.contexto.ast
        nome = str(ast.valor).upper() if ast is not None else "(sem nome)"
        cor = self.cores.get(id(robo), APAGADO)
        self._texto(f"ROBÔ: {nome}", (x, y), cor, self.fonte_titulo)
        if robo is not None:
            self._texto(f"energia {robo.energia}", (x + largura - 90, y + 2))
        y += 22
        meia = largura // 2
        for i, etapa in enumerate(resultado.etapas):
            ex, ey = x + (i % 2) * meia, y + (i // 2) * 18
            cor_etapa = COR_ETAPA.get(etapa.status, APAGADO)
            pygame.draw.rect(self.tela, cor_etapa, (ex, ey + 4, 9, 9))
            self._texto(etapa.nome, (ex + 15, ey), cor_etapa if etapa.status == ERRO else TEXTO)
        y += ((len(resultado.etapas) + 1) // 2) * 18 + 4
        erro = resultado.erro
        if erro is not None:
            onde = f"Linha {erro.linha}: " if erro.linha is not None else ""
            for linha in quebrar_texto(f"{erro.nome.upper()} | {onde}{erro.mensagem}", self.fonte, largura):
                self._texto(linha, (x, y), VERMELHO)
                y += 17
            self._texto("COMPILAÇÃO INTERROMPIDA: fora da batalha", (x, y), VERMELHO)
        elif robo is None:
            self._texto("STATUS: EM CONSTRUÇÃO", (x, y), APAGADO)
        elif not robo.vivo:
            self._texto("STATUS: ELIMINADO", (x, y), APAGADO)
        elif self.arena.tick == 0:
            self._texto("STATUS: PRONTO PARA BATALHA", (x, y), VERDE)
        else:
            self._texto("STATUS: ATIVO", (x, y), VERDE)
        return y + 18

    def _desenhar_resultado(self) -> None:
        vencedor = self.arena.vencedor
        texto = texto_resultado(self.arena, vencedor)
        cor = self.cores[id(vencedor)] if vencedor else TEXTO
        fundo = pygame.Surface((LADO_ARENA, 70), pygame.SRCALPHA)
        fundo.fill((0, 0, 0, 170))
        self.tela.blit(fundo, (0, LADO_ARENA // 2 - 35))
        self._texto(texto, (LADO_ARENA // 2, LADO_ARENA // 2), cor, self.fonte_grande, centro=True)
