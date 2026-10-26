# Desempenho nativo — AssisScript 3.2

2026-10-24T22:03:42.811315+00:00; Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.39; Intel(R) Core(TM) i7-6820HQ CPU @ 2.70GHz; gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0; Python 3.12.3.
5 amostras após um aquecimento; todas as saídas equivalentes verificadas.
Tempos incluem início de processo. C: `-O2 -std=c11 -static`, sem remover verificações no AssisScript.

| Carga | Variante | Mediana (ms) | Mín–máx (ms) |
| --- | --- | ---: | ---: |
| aritmetica | C -O2 | 19.030 | 18.324–25.489 |
| aritmetica | Python | 2922.574 | 2846.698–4553.635 |
| aritmetica | AssisScript | 17.134 | 16.760–18.404 |
| aritmetica | AssisScript --no-opt | 70.400 | 69.589–71.026 |
| aritmetica | AssisScript anterior | 26.855 | 26.611–28.971 |
| collatz | C -O2 | 47.371 | 46.161–48.160 |
| collatz | Python | 3886.639 | 3693.000–4049.920 |
| collatz | AssisScript | 67.542 | 66.516–68.949 |
| collatz | AssisScript --no-opt | 524.264 | 515.113–536.025 |
| collatz | AssisScript anterior | 452.046 | 449.702–462.493 |
| alocacao | C -O2 | 12.522 | 11.928–12.934 |
| alocacao | Python | 353.174 | 344.607–378.289 |
| alocacao | AssisScript | 17.924 | 17.872–18.030 |
| alocacao | AssisScript --no-opt | 18.051 | 17.589–18.697 |
| alocacao | AssisScript anterior | 10874.096 | 10441.967–12293.109 |
| texto-indice | C -O2 | 0.833 | 0.660–0.967 |
| texto-indice | Python | 23.706 | 22.677–24.368 |
| texto-indice | AssisScript | 0.609 | 0.597–0.660 |
| texto-indice | AssisScript --no-opt | 713.445 | 668.169–822.703 |
| texto-indice | AssisScript anterior | 729.012 | 675.652–801.117 |

O teste C de alocação contém uma barreira de compilador sem instruções para impedir que malloc/free sejam eliminados; ela não adiciona acessos volatile. Os laços usam os mesmos limites e resultados. O teste de texto mede a indexação pública com limites verificados em AssisScript e acesso por índice em C/Python. O struct de AssisScript inclui metadados adicionais. O teste de objetos Python usa __slots__.

Cargas abaixo de 20 ms sofrem influência relevante do início do processo; proximidade entre medianas não demonstra paridade com C. Estes quatro programas não representam todos os programas C/C++, nem medem pico de RAM. A variante anterior usa o mesmo fonte com while. Dados brutos acompanham este arquivo.
