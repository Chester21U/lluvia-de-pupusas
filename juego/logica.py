import random
from dataclasses import dataclass

from juego import config


@dataclass
class Jugador:
    x: float
    y: float
    ancho: int = config.JUGADOR_ANCHO
    alto: int = config.JUGADOR_ALTO
    velocidad: float = config.JUGADOR_VELOCIDAD

    def mover(self, direccion, dt):
        self.x += direccion * self.velocidad * dt
        self.x = max(0.0, min(config.ANCHO - self.ancho, self.x))

    @property
    def centro_x(self):
        return self.x + self.ancho / 2


@dataclass
class Objeto:
    x: float
    y: float
    tipo: str
    velocidad: float
    radio: int = config.OBJETO_RADIO

    @property
    def es_bueno(self):
        return self.tipo in config.PUNTOS


def colisiona(jugador, objeto):
    cx = max(jugador.x, min(objeto.x, jugador.x + jugador.ancho))
    cy = max(jugador.y, min(objeto.y, jugador.y + jugador.alto))
    return (objeto.x - cx) ** 2 + (objeto.y - cy) ** 2 <= objeto.radio ** 2


class Partida:
    def __init__(self, semilla=None):
        self.rng = random.Random(semilla)
        self.reiniciar()

    def reiniciar(self):
        self.jugador = Jugador(
            x=(config.ANCHO - config.JUGADOR_ANCHO) / 2,
            y=config.ALTO - config.JUGADOR_ALTO - config.JUGADOR_MARGEN_INFERIOR,
        )
        self.objetos = []
        self.puntaje = 0
        self.vidas = config.VIDAS_INICIALES
        self.nivel = 1
        self.racha = 0
        self.atrapadas = 0
        self.tiempo_spawn = 0.0
        self.terminada = False
        self.eventos = []

    @property
    def multiplicador(self):
        return min(config.MULTIPLICADOR_MAX, 1 + self.racha // config.RACHA_POR_MULTIPLICADOR)

    def intervalo_spawn(self):
        return max(config.SPAWN_MIN, config.SPAWN_BASE - (self.nivel - 1) * config.SPAWN_REDUCCION)

    def velocidad_caida(self):
        return config.CAIDA_BASE + (self.nivel - 1) * config.CAIDA_INCREMENTO

    def probabilidad_chile(self):
        return min(config.PROB_CHILE_MAX, config.PROB_CHILE_BASE + (self.nivel - 1) * config.PROB_CHILE_INCREMENTO)

    def elegir_tipo(self):
        r = self.rng.random()
        if r < config.PROB_DORADA:
            return "dorada"
        if r < config.PROB_DORADA + self.probabilidad_chile():
            return "chile"
        return "pupusa"

    def generar_objeto(self):
        radio = config.OBJETO_RADIO
        x = self.rng.uniform(radio, config.ANCHO - radio)
        velocidad = self.velocidad_caida() * self.rng.uniform(0.85, 1.15)
        self.objetos.append(Objeto(x=x, y=-radio, tipo=self.elegir_tipo(), velocidad=velocidad))

    def actualizar(self, dt, direccion):
        self.eventos = []
        if self.terminada:
            return
        self.jugador.mover(direccion, dt)
        self.tiempo_spawn += dt
        while self.tiempo_spawn >= self.intervalo_spawn():
            self.tiempo_spawn -= self.intervalo_spawn()
            self.generar_objeto()

        restantes = []
        for objeto in self.objetos:
            y_anterior = objeto.y
            objeto.y += objeto.velocidad * dt
            if self.cruzo_comal(objeto, y_anterior) or colisiona(self.jugador, objeto):
                self.atrapar(objeto)
            elif objeto.y - objeto.radio > config.ALTO:
                self.dejar_caer(objeto)
            else:
                restantes.append(objeto)
            if self.terminada:
                break
        self.objetos = restantes if not self.terminada else []
        self.nivel = 1 + self.puntaje // config.PUNTOS_POR_NIVEL

    def cruzo_comal(self, objeto, y_anterior):
        borde = self.jugador.y
        dentro_x = self.jugador.x - objeto.radio <= objeto.x <= self.jugador.x + self.jugador.ancho + objeto.radio
        return dentro_x and y_anterior + objeto.radio < borde and objeto.y - objeto.radio > borde + self.jugador.alto

    def atrapar(self, objeto):
        if objeto.es_bueno:
            self.racha += 1
            self.atrapadas += 1
            puntos = config.PUNTOS[objeto.tipo] * self.multiplicador
            self.puntaje += puntos
            self.eventos.append(("puntos", objeto.tipo, objeto.x, objeto.y, puntos))
        else:
            self.racha = 0
            self.perder_vida(objeto.x, objeto.y, "chile")

    def dejar_caer(self, objeto):
        if objeto.tipo == "pupusa":
            self.racha = 0
            self.perder_vida(objeto.x, config.ALTO - 30, "caida")

    def perder_vida(self, x, y, motivo):
        self.vidas -= 1
        self.eventos.append(("vida", motivo, x, y, -1))
        if self.vidas <= 0:
            self.vidas = 0
            self.terminada = True
            self.eventos.append(("fin", motivo, x, y, 0))
