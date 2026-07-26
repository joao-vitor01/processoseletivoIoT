## Relatório do Candidato

### Identificação do Candidato

- **Nome completo:** João Vitor Lopes Miranda
- **GitHub:** https://github.com/joao-vitor01

---

## Visão Geral da Solução

O projeto implementa um **contador de produção não-intrusivo** para linhas de montagem manuais/semiautomáticas, sem depender de CLPs. Um sensor óptico (LDR) monitora a passagem de peças em uma esteira: quando um objeto interrompe o feixe de luz, o sistema registra a passagem e incrementa a contagem de peças assim que ela passa pelo sensor por completo.

Além disso, o sistema monitora micro-paradas (linha travada por algum tempo), e permite que o operador resete o sistema através de um botão zerando contadores e cronômetros. Toda a telemetria é via Serial (UART).

O usuário interage com o sistema através do botão, a contagem de peças e os alertas são automáticos do firmware.

---

## Arquitetura do Sistema Embarcado

O loop principal `main()` roda de forma não-bloqueante, chamando a cada 10ms as funções:

1. `verificar_sensor_pecas()`- máquina de estados do sensor LDR
2. `verificar_botao_reset()`- máquina de estados do botão com debounce

Nenhuma função é bloqueante além do intervalo curto de polling (10ms), garantindo que o firmware nunca perca janelas de tempo relevantes para os testes.


**Maquina de Estados - Contagem de Peças**

```
[LIVRE] --(luz cai abaixo do limiar)--> [BLOQUEADO] --(luz volta acima do limiar)--> [LIVRE] (+1 na contagem)
                                              |
                                   (tempo bloqueado > 5s)
                                              v
                                    [ALERTA DE MICRO-PARADA]
                                              |
                              (luz volta acima do limiar, +1 na contagem)
                                              v
                                          [LIVRE]
```

- A contagem só é efetivada na borda de subida (quando a peça libera totalmente o sensor), evitando contagem dupla ou parcial.

- Um cronômetro não-bloqueante mede o tempo contínuo; se ultrapassar 5 segundos, emite o alerta de micro-parada uma única vez por evento.

**Máquina de Estados - Botão de reset**

```
[SOLTO] --(pressiona)--> [aguardando debounce ~50ms] --(estavel)--> [PRESSIONADO]
                                    |
                          (ruido: solta antes do debounce)
                                    v
                                [SOLTO]

[PRESSIONADO] --(solta)--> [aguardando debounce ~50ms] --(estavel)--> [SOLTO]
                                                                          |
                                                                  reset dispara aqui
```
O reset é confirmado e disparado na soltura do botão, não no toque inicial, representando um "clique" completo e evitando falsos gatilhos por ruídos mecânicos.

---

## Componentes Utilizados na Simulação

| Componente | ID no diagram.json | Função|
|------------|--------------------|-------|
| Esp32 Devkit C v4 | esp | Microcontrolador Principal |
| Fotorresistor (LDR) | ldr1 | Detecta a passagem de peças |
| Botão | btn1 | Reset manual do turno |
| Monitor Serial | $serialMonitor | Telemetria e logs de status/alerta |


---

## Decisões Técnicas Relevantes

Todas as verificações de tempo usam `time.ticks_ms()`, `time.ticks_diff()` em vez de `sleep_ms()`, garantindo que o firmware tenha um comportamento não-bloqueante.

O botão usa duas variáveis distintas, uma para a última leitura bruta e outra para o último estado confirmado.

Os limiares foram definidos a partir de leituras do ADC do ESP32 nos níveis de teste (800 lux e 50 lux).

O disparo do reset foi movido para o momento de soltar o botão. Após identificar, a partir das análises dos logs, que confirmar o reset ainda durante a pressão fazia a mensagem ser emitida antes do cenário de teste começar a monitorá-lo, o que causava um timeout.

---

## Resultados Obtidos

Os três cenários de teste no Wokwi CI passam com sucesso:

- Cenário 1 - Contagem Normal de Peças: incrementa corretamente ao simular a passagem de uma peça.

- Cenário 2 - Detecção de Micro-paradas: emite o alerta corretamente após o bloqueio contínuo acima do limite de tempo.

- Cenário 3 - Reset Manual de Turno: zera os contadores e emite a mensagem de confirmação ao soltar o botão.

---

## Comentários Adicionais (Opcional)

Algumas execuções do CI falharam por motivos alheios ao código (erros de conexão com a API de simulação do Wokwi), o que reforçou a importância de analisar o log com atenção.