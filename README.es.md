# AssisScript

[English](README.md) · [Português (Brasil)](README.pt-BR.md)

AssisScript es un lenguaje nativo experimental y la base de un proyecto de **nuevo ecosistema Web**. Genera ejecutables para Linux x86_64 y Windows x64. El navegador, HTDL, los estilos y el motor de búsqueda son proyectos futuros.

La implementación usa asistencia de IA (**GPT-6.1 Sol, razonamiento Extra Alto**). La idea, dirección y estructura fueron concebidas por humanos, con ayuda de IA para sugerencias. La revisión y las decisiones permanecen bajo dirección humana.

Versión actual: **3.3.0-alpha.10**, experimental. Consulte [handoff](docs/HANDOFF-3.3-ALPHA.10.md), [validación](docs/VALIDACAO-3.3-ALPHA.10.md) y [progreso](docs/PROGRESSO.md).

## Lenguaje y biblioteca estándar en inglés

Las palabras canónicas y los nombres públicos de módulos, tipos, funciones y miembros de la stdlib deben estar **en inglés**. La documentación puede traducirse; las APIs conservan sus nombres ingleses. Use `fn`, `class`, `main`, `init`, `import`, `File`, `file_open`, `slice_of` y `monotonic_ms`.

Las grafías históricas de la sintaxis siguen como alias del compilador. Los módulos y APIs portugueses se renombraron en alpha.10: siga la [guía](docs/ENGLISH-API.md) y el [mapa](docs/API-MIGRATION.json). Ejecute `assis lock` en proyectos con manifiesto.

```assis
pure fn double(value: int): int { return value * 2; }
safe fn main(): int {
    own values: Array<int> = [1, 2, 3];
    for (let i: int = 0; i < len(values); i += 1) {
        print(double(values[i]));
    }
    return 0;
}
```

En Windows ejecute `instalar-windows.cmd`; en Linux, `sh instalar.sh`. Abra una terminal nueva. Véase la [instalación](docs/INSTALACAO.md).

```sh
assis check hello.assis --safe
assis run hello.assis --safe --debug
assis build hello.assis --safe -o hello
```

Los ejecutables no necesitan Python, Node, GCC ni un ensamblador externo. Reconstruir el compilador requiere C11 y GNU binutils; las pruebas y los paquetes usan Python y Node.

Incluye funciones puras, genéricos, valores de función, registros Copy, enums/matching, Option/Result, ownership, préstamos y vidas explícitas, clases administradas, slices, UTF-8, números nativos, colecciones, archivos, argumentos, JSON limitado, eventos cooperativos, paquetes offline, editor/LSP y depuración Linux.

Módulos: `math`, `strings`, `memory`, `errors`, `convert`, `algorithms`, `csv`, `encoding`, `cli`, `json`, `time`, `log`, `iterators`, `events`, `unicode`, `owned`. Véase el [catálogo](stdlib/catalogo.json).

Siguen pendientes closures/capturas, variantes Move, FFI C, red/DNS/HTTP/TLS, aplicaciones B/C completas, 24 horas reales de validación, backend completo por IR, ARM64/macOS y aceptación independiente. `--safe` es explícito. El porcentaje no certifica madurez para producción.

## Uso, bibliotecas y forks

El responsable eligió **CC BY-NC-SA 4.0** para los materiales originales. Consulte [LICENSE](LICENSE), la [licencia oficial](https://creativecommons.org/licenses/by-nc-sa/4.0/), [procedencia](docs/PROCEDENCIA.md) y [avisos de terceros](THIRD_PARTY_NOTICES.md).

1. No se concede uso comercial de los materiales licenciados. Solicite permiso separado cuando la licencia o la ley no permitan el uso previsto.
2. Se permite crear bibliotecas. Las independientes pueden declarar su licencia; las que incorporan material del proyecto deben respetar los términos aplicables de atribución, uso no comercial y ShareAlike. Las contribuciones usan APIs en inglés.
3. Los forks/adaptaciones redistribuidos deben acreditar a **Vibe-O-Coder / AssisScript**, enlazar al [original](https://github.com/Vibe-O-Coder/AssisScript), conservar avisos, identificar cambios y cumplir ShareAlike. Distinga versiones no oficiales y no sugiera aprobación.
4. Estas notas no añaden restricciones ni cambian licencias de terceros. Compilar código independiente no lo relicencia automáticamente; el material copiado o incorporado, incluido el runtime, conserva sus términos.
5. No hay garantía. Informe defectos en [issues](https://github.com/Vibe-O-Coder/AssisScript/issues). Consulte la [política de soporte](docs/SUPPORT.md).
