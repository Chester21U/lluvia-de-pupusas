import json

from juego import config
from juego.logica import Jugador, Objeto, Partida, colisiona
from juego.records import cargar_record, guardar_record


def objeto_sobre_comal(partida, tipo):
    j = partida.jugador
    return Objeto(x=j.centro_x, y=j.y - 1, tipo=tipo, velocidad=100)


def test_jugador_no_sale_por_la_izquierda():
    j = Jugador(x=10, y=500)
    j.mover(-1, 1.0)
    assert j.x == 0


def test_jugador_no_sale_por_la_derecha():
    j = Jugador(x=config.ANCHO - 130, y=500)
    j.mover(1, 1.0)
    assert j.x == config.ANCHO - j.ancho


def test_movimiento_independiente_de_fps():
    a = Jugador(x=300, y=500)
    b = Jugador(x=300, y=500)
    for _ in range(30):
        a.mover(1, 1 / 30)
    for _ in range(60):
        b.mover(1, 1 / 60)
    assert abs(a.x - b.x) < 1e-6


def test_colision_detecta_contacto_y_ausencia():
    j = Jugador(x=100, y=500)
    assert colisiona(j, Objeto(x=150, y=490, tipo="pupusa", velocidad=0))
    assert not colisiona(j, Objeto(x=400, y=490, tipo="pupusa", velocidad=0))


def test_atrapar_pupusa_suma_puntos():
    p = Partida(semilla=1)
    p.objetos = [objeto_sobre_comal(p, "pupusa")]
    p.actualizar(0.01, 0)
    assert p.puntaje == config.PUNTOS["pupusa"]
    assert p.vidas == config.VIDAS_INICIALES


def test_pupusa_dorada_vale_mas():
    p = Partida(semilla=1)
    p.objetos = [objeto_sobre_comal(p, "dorada")]
    p.actualizar(0.01, 0)
    assert p.puntaje == config.PUNTOS["dorada"]


def test_atrapar_chile_quita_vida_y_reinicia_racha():
    p = Partida(semilla=1)
    p.racha = 7
    p.objetos = [objeto_sobre_comal(p, "chile")]
    p.actualizar(0.01, 0)
    assert p.vidas == config.VIDAS_INICIALES - 1
    assert p.racha == 0


def test_pupusa_que_cae_al_suelo_quita_vida():
    p = Partida(semilla=1)
    p.objetos = [Objeto(x=20, y=config.ALTO + config.OBJETO_RADIO, tipo="pupusa", velocidad=200)]
    p.jugador.x = config.ANCHO - p.jugador.ancho
    p.actualizar(0.05, 0)
    assert p.vidas == config.VIDAS_INICIALES - 1


def test_chile_que_cae_no_castiga():
    p = Partida(semilla=1)
    p.objetos = [Objeto(x=20, y=config.ALTO + config.OBJETO_RADIO, tipo="chile", velocidad=200)]
    p.jugador.x = config.ANCHO - p.jugador.ancho
    p.actualizar(0.05, 0)
    assert p.vidas == config.VIDAS_INICIALES


def test_objeto_rapido_no_atraviesa_el_comal():
    p = Partida(semilla=1)
    j = p.jugador
    p.objetos = [Objeto(x=j.centro_x, y=j.y - 40, tipo="pupusa", velocidad=6000)]
    p.actualizar(0.05, 0)
    assert p.puntaje == config.PUNTOS["pupusa"]


def test_partida_termina_sin_vidas():
    p = Partida(semilla=1)
    p.vidas = 1
    p.objetos = [objeto_sobre_comal(p, "chile")]
    p.actualizar(0.01, 0)
    assert p.terminada
    assert p.vidas == 0
    assert p.objetos == []


def test_multiplicador_por_racha():
    p = Partida(semilla=1)
    p.racha = config.RACHA_POR_MULTIPLICADOR
    assert p.multiplicador == 2
    p.racha = 1000
    assert p.multiplicador == config.MULTIPLICADOR_MAX


def test_nivel_aumenta_dificultad():
    p = Partida(semilla=1)
    vel1, spawn1 = p.velocidad_caida(), p.intervalo_spawn()
    p.puntaje = config.PUNTOS_POR_NIVEL * 3
    p.actualizar(0.001, 0)
    assert p.nivel == 4
    assert p.velocidad_caida() > vel1
    assert p.intervalo_spawn() < spawn1


def test_reiniciar_restablece_estado():
    p = Partida(semilla=1)
    p.puntaje, p.vidas, p.terminada = 500, 0, True
    p.reiniciar()
    assert (p.puntaje, p.vidas, p.terminada, p.objetos) == (0, config.VIDAS_INICIALES, False, [])


def test_simulacion_larga_sin_errores():
    p = Partida(semilla=42)
    for i in range(20000):
        p.actualizar(1 / 60, 1 if (i // 90) % 2 else -1)
        if p.terminada:
            p.reiniciar()
    assert p.vidas >= 0


def test_record_archivo_inexistente(tmp_path):
    assert cargar_record(tmp_path / "no_existe.json") == 0


def test_record_archivo_corrupto(tmp_path):
    ruta = tmp_path / "record.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert cargar_record(ruta) == 0


def test_record_guardar_y_cargar(tmp_path):
    ruta = tmp_path / "sub" / "record.json"
    assert guardar_record(340, ruta)
    assert json.loads(ruta.read_text(encoding="utf-8")) == {"record": 340}
    assert cargar_record(ruta) == 340
