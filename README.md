# Analizar DAB

[![FIJI](https://img.shields.io/badge/Programa-FIJI%2FImageJ-blue.svg)](https://imagej.net/software/fiji/)
[![Licencia](https://img.shields.io/badge/Licencia-BSD--3--Clause-green.svg)](LICENSE)
[![Java](https://img.shields.io/badge/Java-8%2B-orange.svg)](https://adoptium.net/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23604119.svg)](https://doi.org/10.5281/zenodo.23604119)

<div align="center">
<img src="docs/Analizar DAB logo design-Final.png" width="300">
</div>

<div align="justify">
  
- Herramienta desarrollada para FIJI/ImageJ que automatiza la cuantificación de la señal de diaminobencidina (DAB) en imágenes de tejido obtenidas mediante microscopía óptica de campo claro.

---

## ⚠️ Requiere FIJI / ImageJ actualizado.
- Descargalo en: [FIJI/ImageJ](https://imagej.net/software/fiji/downloads)

---

## ⬇️ Descarga

Descargá la última versión del `.jar` desde la sección **Releases** de este repositorio.

- ⬇️ **[Ir a Releases](https://github.com/ezegrondona/Analizar-DAB/releases)**

---

## 🔧 Instalación

1. Descargar el `.jar`.
2. Copiarlo en la carpeta `plugins/` de tu instalación de FIJI.
3. Reiniciar FIJI.
4. El plugin aparecerá en el menú `Plugins`.

---

## 📋 Guía Completa

- [Descargar Guía](https://is.gd/6r8oD6)

O desde **"GUIA DE USO"** una vez abierto el plugin.

---

## 👤 Autor

- **Autor:** Dr. Ezequiel Grondona
- **Institución:** Centro de Microscopía Electrónica — UNC / INICSA / CONICET
- **Contacto:** 📧 ezequiel.grondona@unc.edu.ar

---

## 🔨 Compilar desde el código

El complemento es un proyecto Maven. Con Java 8 o superior y Maven
instalados:

```
mvn clean package
```

El `.jar` listo para usar queda en `target/`. Incluye adentro las
bibliotecas que necesita —Apache POI, Log4j y sus dependencias—, así
que se copia a `plugins/` y funciona.

ImageJ no se empaqueta: la aporta la instalación de FIJI donde se
instale el complemento.

---

## 📑 Cómo citar

Si usás Analizar DAB en un trabajo publicado, citalo. Para una
herramienta científica, la cita es lo que permite que el trabajo de
construirla se reconozca y que otro pueda reproducir lo que hiciste.

> Grondona, E. (2026). *Analizar DAB* [software]. Centro de
> Microscopía Electrónica, Universidad Nacional de Córdoba — INICSA
> (CONICET–UNC). https://doi.org/10.5281/zenodo.23604119

El repositorio incluye un archivo [`CITATION.cff`](CITATION.cff):
GitHub lo lee y muestra el botón **«Cite this repository»** arriba a
la derecha, que da la cita ya formateada en APA y en BibTeX.

**Sobre el DOI.** El de arriba es el *concept DOI*: apunta siempre a
la versión más reciente, así que una cita hecha hoy sigue sirviendo
cuando se publique una versión nueva. Si necesitás citar una versión
puntual —por ejemplo para que otro reproduzca exactamente tu análisis—
la 1.0.0 tiene el suyo: [10.5281/zenodo.23604120](https://doi.org/10.5281/zenodo.23604120).

---

## 📄 Licencia

**BSD 3-Clause.** Podés usar, modificar, redistribuir e incluso vender
obras derivadas, con dos condiciones: conservar el aviso de copyright
y la licencia, y no usar el nombre del autor ni el de la institución
para promocionar derivados sin permiso. El texto completo está en
[`LICENSE`](LICENSE).

El `.jar` que se distribuye empaqueta bibliotecas de terceros que
conservan sus propias licencias, todas permisivas y compatibles. Están
detalladas en [`THIRD-PARTY-NOTICES.txt`](THIRD-PARTY-NOTICES.txt).

</div>
