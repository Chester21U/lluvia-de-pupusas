import sys

import pygame

from juego import config
from juego.logica import Partida
from juego.records import cargar_record, guardar_record

MANCHAS = [(-0.35, -0.25, 0.18), (0.30, -0.10, 0.14), (-0.05, 0.35, 0.16), (0.40, 0.35, 0.10), (-0.45, 0.20, 0.09)]


class TextoFlotante:
    def __init__(self, texto, x, y, color):
        self.texto = texto
        self.x = x
        self.y = y
        self.color = color
        self.vida = 0.9

    def actualizar(self, dt):
        self.y -= 70 * dt
        self.vida -= dt


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(config.TITULO)
        self.pantalla = pygame.display.set_mode((config.ANCHO, config.ALTO))
        self.reloj = pygame.time.Clock()
        self.fuente_titulo = pygame.font.Font(None, 92)
        self.fuente_grande = pygame.font.Font(None, 48)
        self.fuente = pygame.font.Font(None, 34)
        self.fuente_chica = pygame.font.Font(None, 26)
        self.partida = Partida()
        self.record = cargar_record()
        self.nuevo_record = False
        self.estado = "menu"
        self.textos = []
        self.sacudida = 0.0
        self.fondo = self.crear_fondo()

    def crear_fondo(self):
        fondo = pygame.Surface((config.ANCHO, config.ALTO))
        arriba, abajo = config.COLOR_CIELO_ARRIBA, config.COLOR_CIELO_ABAJO
        for y in range(config.ALTO):
            t = y / config.ALTO
            color = tuple(int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(3))
            pygame.draw.line(fondo, color, (0, y), (config.ANCHO, y))
        for i, (x, y) in enumerate([(80, 60), (210, 120), (350, 40), (520, 90), (690, 50), (760, 140), (150, 200), (620, 180)]):
            pygame.draw.circle(fondo, (255, 240, 210), (x, y), 2 if i % 2 else 1)
        pygame.draw.rect(fondo, config.COLOR_SUELO, (0, config.ALTO - 18, config.ANCHO, 18))
        pygame.draw.line(fondo, (130, 85, 60), (0, config.ALTO - 18), (config.ANCHO, config.ALTO - 18), 3)
        return fondo

    def iniciar(self):
        self.partida.reiniciar()
        self.textos = []
        self.nuevo_record = False
        self.estado = "jugando"

    def finalizar(self):
        if self.partida.puntaje > self.record:
            self.record = self.partida.puntaje
            self.nuevo_record = True
            guardar_record(self.record)
        self.estado = "game_over"

    def salir(self):
        pygame.quit()
        sys.exit()

    def manejar_evento(self, evento):
        if evento.type == pygame.QUIT:
            self.salir()
        if evento.type != pygame.KEYDOWN:
            return
        tecla = evento.key
        if self.estado == "menu":
            if tecla in (pygame.K_RETURN, pygame.K_SPACE):
                self.iniciar()
            elif tecla == pygame.K_ESCAPE:
                self.salir()
        elif self.estado == "jugando":
            if tecla in (pygame.K_p, pygame.K_ESCAPE):
                self.estado = "pausa"
        elif self.estado == "pausa":
            if tecla in (pygame.K_p, pygame.K_ESCAPE):
                self.estado = "jugando"
            elif tecla == pygame.K_q:
                self.estado = "menu"
        elif self.estado == "game_over":
            if tecla in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self.iniciar()
            elif tecla == pygame.K_ESCAPE:
                self.estado = "menu"

    def leer_direccion(self):
        teclas = pygame.key.get_pressed()
        derecha = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]
        izquierda = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        return int(derecha) - int(izquierda)

    def paso(self, dt, direccion):
        if self.estado == "jugando":
            self.partida.actualizar(dt, direccion)
            self.procesar_eventos()
            if self.partida.terminada:
                self.finalizar()
        for texto in self.textos:
            texto.actualizar(dt)
        self.textos = [t for t in self.textos if t.vida > 0]
        self.sacudida = max(0.0, self.sacudida - dt)

    def procesar_eventos(self):
        for tipo, detalle, x, y, valor in self.partida.eventos:
            if tipo == "puntos":
                color = config.COLOR_DORADA if detalle == "dorada" else config.COLOR_TEXTO
                self.textos.append(TextoFlotante(f"+{valor}", x, y, color))
            elif tipo == "vida":
                mensaje = "¡Chile!" if detalle == "chile" else "¡Se cayó!"
                self.textos.append(TextoFlotante(mensaje, x, y, config.COLOR_PELIGRO))
                self.sacudida = 0.25

    def ejecutar(self):
        while True:
            dt = min(self.reloj.tick(config.FPS) / 1000, 0.05)
            for evento in pygame.event.get():
                self.manejar_evento(evento)
            self.paso(dt, self.leer_direccion())
            self.dibujar()
            pygame.display.flip()

    def texto(self, contenido, fuente, color, centro=None, esquina=None):
        sombra = fuente.render(contenido, True, config.COLOR_SOMBRA)
        superficie = fuente.render(contenido, True, color)
        rect = superficie.get_rect()
        if centro:
            rect.center = centro
        else:
            rect.topleft = esquina
        self.lienzo.blit(sombra, rect.move(2, 2))
        self.lienzo.blit(superficie, rect)
        return rect

    def dibujar_pupusa(self, x, y, radio, dorada=False):
        base = config.COLOR_DORADA if dorada else config.COLOR_MASA
        borde = config.COLOR_DORADA_BORDE if dorada else config.COLOR_MASA_BORDE
        pygame.draw.ellipse(self.lienzo, (0, 0, 0, 60), (x - radio, y - radio * 0.55 + 6, radio * 2, radio * 1.3))
        pygame.draw.circle(self.lienzo, borde, (int(x), int(y)), radio)
        pygame.draw.circle(self.lienzo, base, (int(x), int(y)), radio - 3)
        for dx, dy, r in MANCHAS:
            pygame.draw.circle(self.lienzo, borde if dorada else config.COLOR_QUEMADITO, (int(x + dx * radio), int(y + dy * radio)), max(2, int(r * radio)))
        if dorada:
            pygame.draw.circle(self.lienzo, (255, 250, 210), (int(x - radio * 0.35), int(y - radio * 0.4)), 3)

    def dibujar_chile(self, x, y, radio):
        cuerpo = pygame.Rect(0, 0, int(radio * 1.1), int(radio * 2.1))
        cuerpo.center = (int(x), int(y + 2))
        pygame.draw.ellipse(self.lienzo, (140, 20, 20), cuerpo.inflate(4, 4))
        pygame.draw.ellipse(self.lienzo, config.COLOR_CHILE, cuerpo)
        pygame.draw.ellipse(self.lienzo, (255, 120, 110), (cuerpo.x + 4, cuerpo.y + 6, 4, cuerpo.height // 3))
        pygame.draw.rect(self.lienzo, config.COLOR_TALLO, (int(x) - 3, cuerpo.top - 8, 6, 10), border_radius=2)
        pygame.draw.ellipse(self.lienzo, config.COLOR_TALLO, (int(x) - 9, cuerpo.top - 3, 18, 7))

    def dibujar_comal(self):
        j = self.partida.jugador
        pygame.draw.rect(self.lienzo, (70, 45, 35), (j.x - 16, j.y + 6, 18, 8), border_radius=3)
        pygame.draw.rect(self.lienzo, (70, 45, 35), (j.x + j.ancho - 2, j.y + 6, 18, 8), border_radius=3)
        pygame.draw.ellipse(self.lienzo, config.COLOR_COMAL_BORDE, (j.x, j.y, j.ancho, j.alto))
        pygame.draw.ellipse(self.lienzo, config.COLOR_COMAL, (j.x + 4, j.y + 3, j.ancho - 8, j.alto - 6))
        brasas = [(0.2, 255, 120), (0.45, 255, 80), (0.7, 255, 140), (0.88, 230, 90)]
        for t, r, g in brasas:
            pygame.draw.circle(self.lienzo, (r, g, 30), (int(j.x + j.ancho * t), int(j.y + j.alto + 8)), 4)

    def dibujar_corazon(self, x, y, lleno):
        color = config.COLOR_PELIGRO if lleno else (90, 70, 80)
        pygame.draw.circle(self.lienzo, color, (x - 5, y), 7)
        pygame.draw.circle(self.lienzo, color, (x + 5, y), 7)
        pygame.draw.polygon(self.lienzo, color, [(x - 12, y + 2), (x + 12, y + 2), (x, y + 15)])

    def dibujar_hud(self):
        barra = pygame.Surface((config.ANCHO, 52), pygame.SRCALPHA)
        barra.fill((20, 10, 30, 150))
        self.lienzo.blit(barra, (0, 0))
        p = self.partida
        self.texto(f"Puntos: {p.puntaje}", self.fuente, config.COLOR_TEXTO, esquina=(16, 8))
        self.texto(f"Récord: {max(self.record, p.puntaje)}", self.fuente_chica, config.COLOR_ACENTO, esquina=(16, 32))
        self.texto(f"Nivel {p.nivel}", self.fuente, config.COLOR_TEXTO, centro=(config.ANCHO // 2, 18))
        if p.multiplicador > 1:
            self.texto(f"Racha x{p.multiplicador}", self.fuente_chica, config.COLOR_ACENTO, centro=(config.ANCHO // 2, 40))
        for i in range(config.VIDAS_INICIALES):
            self.dibujar_corazon(config.ANCHO - 30 - i * 34, 20, i < p.vidas)

    def dibujar_capa(self, alfa=170):
        capa = pygame.Surface((config.ANCHO, config.ALTO), pygame.SRCALPHA)
        capa.fill((15, 8, 25, alfa))
        self.lienzo.blit(capa, (0, 0))

    def dibujar_menu(self):
        self.dibujar_capa(120)
        cx = config.ANCHO // 2
        self.texto("Lluvia de", self.fuente_grande, config.COLOR_TEXTO, centro=(cx, 130))
        self.texto("PUPUSAS", self.fuente_titulo, config.COLOR_ACENTO, centro=(cx, 190))
        for i, x in enumerate([cx - 190, cx - 95, cx + 95, cx + 190]):
            self.dibujar_pupusa(x, 270 + (i % 2) * 14, 22, dorada=(i == 2))
        self.dibujar_chile(cx, 278, 20)
        lineas = [
            ("Atrapá las pupusas con el comal (+10)", config.COLOR_TEXTO),
            ("Las doradas valen +50", config.COLOR_DORADA),
            ("Esquivá los chiles y no dejés caer pupusas", config.COLOR_PELIGRO),
            ("Moverse: Flechas o A / D     Pausa: P o ESC", config.COLOR_TEXTO),
        ]
        for i, (linea, color) in enumerate(lineas):
            self.texto(linea, self.fuente_chica, color, centro=(cx, 345 + i * 30))
        self.texto("Presioná ENTER para empezar", self.fuente, config.COLOR_ACENTO, centro=(cx, 490))
        self.texto(f"Récord actual: {self.record}", self.fuente_chica, config.COLOR_TEXTO, centro=(cx, 530))

    def dibujar_pausa(self):
        self.dibujar_capa()
        cx = config.ANCHO // 2
        self.texto("PAUSA", self.fuente_titulo, config.COLOR_ACENTO, centro=(cx, 250))
        self.texto("P o ESC para continuar  ·  Q para volver al menú", self.fuente_chica, config.COLOR_TEXTO, centro=(cx, 320))

    def dibujar_game_over(self):
        self.dibujar_capa()
        cx = config.ANCHO // 2
        p = self.partida
        self.texto("¡SE ACABÓ!", self.fuente_titulo, config.COLOR_PELIGRO, centro=(cx, 180))
        self.texto(f"Puntaje: {p.puntaje}", self.fuente_grande, config.COLOR_TEXTO, centro=(cx, 260))
        self.texto(f"Pupusas atrapadas: {p.atrapadas}   ·   Nivel alcanzado: {p.nivel}", self.fuente_chica, config.COLOR_TEXTO, centro=(cx, 305))
        if self.nuevo_record:
            self.texto("¡Nuevo récord!", self.fuente, config.COLOR_ACENTO, centro=(cx, 350))
        else:
            self.texto(f"Récord: {self.record}", self.fuente, config.COLOR_ACENTO, centro=(cx, 350))
        self.texto("R o ENTER para jugar otra vez  ·  ESC para el menú", self.fuente_chica, config.COLOR_TEXTO, centro=(cx, 420))

    def dibujar(self):
        self.lienzo = pygame.Surface((config.ANCHO, config.ALTO))
        self.lienzo.blit(self.fondo, (0, 0))
        if self.estado == "menu":
            self.dibujar_menu()
        else:
            for objeto in self.partida.objetos:
                if objeto.tipo == "chile":
                    self.dibujar_chile(objeto.x, objeto.y, objeto.radio)
                else:
                    self.dibujar_pupusa(objeto.x, objeto.y, objeto.radio, objeto.tipo == "dorada")
            self.dibujar_comal()
            for t in self.textos:
                self.texto(t.texto, self.fuente, t.color, centro=(int(t.x), int(t.y)))
            self.dibujar_hud()
            if self.estado == "pausa":
                self.dibujar_pausa()
            elif self.estado == "game_over":
                self.dibujar_game_over()
        desplazamiento = (int(6 * self.sacudida * 4) * (1 if pygame.time.get_ticks() // 30 % 2 else -1), 0) if self.sacudida > 0 else (0, 0)
        self.pantalla.fill((0, 0, 0))
        self.pantalla.blit(self.lienzo, desplazamiento)


def main():
    App().ejecutar()
