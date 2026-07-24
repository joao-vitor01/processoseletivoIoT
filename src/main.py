from machine import Pin, ADC
import time

#Configurando os pinos conforme o diagrama
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB) #Faixa de leitura 0-3.3V (0-4095)

btn_reset = Pin(4, Pin.IN, Pin.PULL_UP) #Pressionado =0, (pull_up)

#Parâmetros do sistema
LIMIAR_LIVRE_ADC = 1200 #Leitura abaixo disso = ambiente claro = linha livre
LIMIAR_BLOQUEIO_ADC = 2000 #Leitura acima disso = ambiente escuro = peça bloqueada
TEMPO_MICROPARADAS_MS = 5000
DEBOUNCE_MS = 50
INTERVALO_LOOP_MS = 10 # polling curto, não bloqueante

DEBUG_CALIBRACAO = False
DEBUG_INTERVALO_MS = 300 #evita spammar o serial a cada 10ms
_ultimo_debug_ms = 0

#--Estado Global--
contador_pecas = 0
estado_livre = True
tempo_inicio_bloqueio = None
alerta_microparada_emitido = False

ultimo_estado_botao = 1
estado_botao_estavel = 1
tempo_ultima_mudanca_botao = time.ticks_ms()

def ler_luminosidade():
    #Le o valor bruto do ADC ligado ao LDR (0-4095 no ESP32)
    return ldr.read()

def verificar_sensor_pecas():
    global estado_livre, tempo_inicio_bloqueio, alerta_microparada_emitido, contador_pecas

    tempo_atual = time.ticks_ms()
    valor_ldr = ler_luminosidade()

    if estado_livre and valor_ldr > LIMIAR_BLOQUEIO_ADC:
        estado_livre = False
        tempo_inicio_bloqueio = tempo_atual
        alerta_microparada_emitido = False

    elif not estado_livre and valor_ldr < LIMIAR_LIVRE_ADC:
        estado_livre = True
        tempo_inicio_bloqueio = None
        contador_pecas += 1
        print("Peca detectada! Total: {}".format(contador_pecas))

    elif not estado_livre and tempo_inicio_bloqueio is not None:
        decorrido = time.ticks_diff(tempo_atual, tempo_inicio_bloqueio)
        if decorrido >= TEMPO_MICROPARADAS_MS and not alerta_microparada_emitido:
            print("Alerta: Micro-parada detectada!")
            alerta_microparada_emitido = True

def verificar_botao_reset():
    global contador_pecas, estado_livre, tempo_ultima_mudanca_botao, ultimo_estado_botao, estado_botao_estavel, tempo_inicio_bloqueio, alerta_microparada_emitido

    leitura_botao = btn_reset.value()
    tempo_agora = time.ticks_ms()

    if leitura_botao != ultimo_estado_botao:
        # mudanca na leitura bruta: reinicia o timer de debounce
        tempo_ultima_mudanca_botao = tempo_agora
        ultimo_estado_botao = leitura_botao

    if time.ticks_diff(tempo_agora, tempo_ultima_mudanca_botao) > DEBOUNCE_MS:
        # leitura ficou estavel pelo tempo de debounce: confirma a transicao
        if leitura_botao == 0 and estado_botao_estavel == 1:
            contador_pecas = 0
            estado_livre = True
            tempo_inicio_bloqueio = None
            alerta_microparada_emitido = False
            print("Turno resetado com sucesso. Contadores zerados.")
        estado_botao_estavel = leitura_botao


def main():
    print("Contador de Producao Inicializado")
    while True:
        verificar_sensor_pecas()
        verificar_botao_reset()
        time.sleep_ms(INTERVALO_LOOP_MS)
if __name__ == "__main__":
    main()