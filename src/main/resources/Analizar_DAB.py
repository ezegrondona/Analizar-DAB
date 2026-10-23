from ij import IJ, WindowManager, ImagePlus
from ij.io import DirectoryChooser, OpenDialog, SaveDialog
from ij.measure import ResultsTable
from ij.text import TextWindow
from ij.gui import GenericDialog, Roi
import java.awt.Desktop as Desktop
import java.net.URI as URI
from java.awt import Color, Font, Button, Panel, GridLayout
import os
import time
import jarray

# ==========================================================================
#  VARIABLES GLOBALES
# ==========================================================================
ir_a_calibrar = False

# Modelo estadístico: arrays de 16384 entradas (128 x 128 bins CbCr)
prob_brown    = [0.0] * 16384   # Probabilidad de color positivo (DAB)
prob_nonbrown = [0.0] * 16384   # Probabilidad de color negativo
modelo_cargado = False
ir_a_entrenar = False


# ==========================================================================
#  FUNCIONES AUXILIARES GENERALES
# ==========================================================================

def mostrar_info_plugin(_event=None):
    """Muestra la ventana de información del plugin con imagen."""
    gd = GenericDialog("Informacion del Plugin")
    
    try:
        # Intentar obtener la ruta del script para encontrar el logo
        import inspect
        script_path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        img_path = os.path.join(script_path, "Analizar DAB logo design-Final.png")
        
        # Fallback a la carpeta de plugins si no se encuentra
        if not os.path.exists(img_path):
             img_path = IJ.getDirectory("plugins") + "Analizar_DAB" + os.sep + "Analizar DAB logo design-Final.png"
             
        imp_logo = IJ.openImage(img_path)
        if imp_logo:
             ip = imp_logo.getProcessor()
             ip.setInterpolationMethod(1) # 1 = BILINEAR
             w = 300
             h = int(float(ip.getHeight()) / float(ip.getWidth()) * w)
             imp_resized = ImagePlus("Logo", ip.resize(w, h))
             gd.addImage(imp_resized)
    except:
        pass

    info_texto = ("<html><center><br>"
                  "<h3>Analizar DAB</h3>"
                  "Analisis Cuantitativo de Inmunohistoquimicas.<br><br>"
                  "<b>Creado por:</b><br>"
                  "<b>Dr. Ezequiel Grondona</b><br>"
                  "-UNC - INICSA - CONICET-<br>"
                  "- 2026 -<br><br>"
                  "Lea atentamente la guia de uso antes de utilizar el plugin.<br>"
                  "Consultas y sugerencias:<br>"
                  "ezequiel.grondona@unc.edu.ar<br>"
                  "</center></html>")
    
    from javax.swing import JLabel
    from java.awt import Panel
    panel = Panel()
    label = JLabel(info_texto)
    panel.add(label)
    gd.addPanel(panel)
    
    estilizar_dialogo(gd)
    gd.showDialog()


def abrir_guia(_event=None):
    """Abre la guía de uso en el navegador."""
    try:
        url = "https://codeberg.org/ezegrondona/Analizar-DAB/raw/branch/main/docs/Gu%C3%ADa%20de%20Uso%20-%20Analizar%20DAB.pdf"
        Desktop.getDesktop().browse(URI(url))
    except Exception as e:
        IJ.showMessage("Error", "No se pudo abrir el enlace:\n{}".format(e))


def abrir_ayuda(_event=None):
    """Abre el manual de calibracion en el navegador."""
    try:
        url = "https://codeberg.org/ezegrondona/Analizar-DAB/raw/branch/main/docs/Gu%C3%ADa%20de%20Calibraci%C3%B3n%20FIJI-ImajeJ.pdf"
        Desktop.getDesktop().browse(URI(url))
    except Exception as e:
        IJ.showMessage("Error", "No se pudo abrir el enlace:\n{}".format(e))


def abrir_calibracion(_event=None):
    """Cierra el dialogo principal y activa la bandera para calibracion."""
    global ir_a_calibrar
    ir_a_calibrar = True
    try:
        source = _event.getSource()
        parent = source.getParent()
        while parent is not None:
            if isinstance(parent, GenericDialog):
                parent.dispose()
                break
            parent = parent.getParent()
    except Exception:
        pass


# ==========================================================================
#  FUNCIONES DE ESTILO (basadas en "6- Estructura y Estética")
# ==========================================================================

def estilizar_dialogo(gd, es_principal=False,
                      btn_info=None, btn_guia=None,
                      btn_manual=None, btn_calibrar=None,
                      btn_entrenar=None, btn_cargar=None):

    font_msg     = Font("SansSerif", Font.PLAIN, 12)
    font_btn     = Font("SansSerif", Font.PLAIN, 10)
    font_btn1    = Font("SansSerif", Font.BOLD, 10)
    font_section = Font("SansSerif", Font.BOLD, 13)

    # COLORES
    color_manual   = Color(157, 167, 159)
    color_calibrar = Color(25, 136, 255)    # Azul para TODAS las secciones
    color_info     = Color(0, 151, 161)
    color_dab      = Color(180, 120, 50)     # Marrón DAB solo para botones de entrenamiento
    color_blanco   = Color.WHITE

    palabras_seccion = ["DETERMINACIONES", "MEDICION", "CALIBRACION", "ENTRENAMIENTO DAB"]
    palabras_centrar = ["INFO DEL PLUGIN"]

    layout = gd.getLayout()
    tiene_constraints = hasattr(layout, 'getConstraints')

    # Estilizar botones INFO y GUIA
    if btn_info is not None:
        btn_info.setFont(font_btn)
        btn_info.setForeground(Color.WHITE)
        btn_info.setBackground(color_info)
    if btn_guia is not None:
        btn_guia.setFont(font_btn1)
        btn_guia.setForeground(Color.WHITE)
        btn_guia.setBackground(color_info)

    # Estilizar botones MANUAL y CALIBRAR
    if btn_manual is not None:
        btn_manual.setFont(font_btn)
        btn_manual.setForeground(Color.WHITE)
        btn_manual.setBackground(color_manual)
    if btn_calibrar is not None:
        btn_calibrar.setFont(font_btn)
        btn_calibrar.setForeground(Color.WHITE)
        btn_calibrar.setBackground(color_manual)

    # Estilizar botones ENTRENAR y CARGAR
    if btn_entrenar is not None:
        btn_entrenar.setFont(font_btn1)
        btn_entrenar.setForeground(Color.WHITE)
        btn_entrenar.setBackground(color_manual)
    if btn_cargar is not None:
        btn_cargar.setFont(font_btn1)
        btn_cargar.setForeground(Color.WHITE)
        btn_cargar.setBackground(color_manual)

    # Estilizar componentes del diálogo
    for comp in gd.getComponents():
        comp_str = str(type(comp))

        if "Label" in comp_str:
            try:
                texto = comp.getText() if hasattr(comp, 'getText') else ""
                comp.setFont(font_msg)

                es_centrado = any(p in texto.upper() for p in palabras_centrar)
                if es_centrado and texto.strip():
                    try:
                        if hasattr(comp, 'setAlignment'):
                            comp.setAlignment(1)
                    except Exception:
                        pass

                es_seccion = any(p in texto.upper() for p in palabras_seccion) or "INFORMACIÓN" in texto.upper()
                if es_seccion and texto.strip():
                    comp.setFont(font_section)
                    try:
                        comp.setBackground(color_dab)
                        comp.setForeground(color_blanco)
                    except Exception:
                        try:
                            comp.setOpaque(True)
                            comp.setBackground(color_dab)
                            comp.setForeground(color_blanco)
                        except Exception:
                            pass
                    try:
                        if hasattr(comp, 'setAlignment'):
                            comp.setAlignment(1)
                        if tiene_constraints:
                            cons = layout.getConstraints(comp)
                            if cons is not None:
                                cons.fill = 2
                                cons.insets.left = 10
                                cons.insets.right = 10
                                layout.setConstraints(comp, cons)
                    except Exception:
                        pass
            except Exception:
                pass

        elif isinstance(comp, Button):
            try:
                label = comp.getLabel()
                comp.setFont(font_btn)
                comp.setForeground(Color.WHITE)
                if "MANUAL" in label.upper() or "CALIBRAR" in label.upper():
                    comp.setBackground(color_manual)
                elif "INFO" in label.upper() or "GUIA" in label.upper() or u"GUÍA" in label.upper():
                    comp.setBackground(color_info)
                elif "ENTRENAR" in label.upper() or "CARGAR" in label.upper():
                    comp.setBackground(color_dab)
                elif "OK" in label.upper():
                    comp.setBackground(color_manual)
                else:
                    comp.setBackground(Color.LIGHT_GRAY)
            except Exception:
                pass

        elif isinstance(comp, Panel):
            try:
                if tiene_constraints:
                    cons = layout.getConstraints(comp)
                    if cons is not None:
                        cons.fill = 2
                        cons.insets.left = 10
                        cons.insets.right = 10
                        layout.setConstraints(comp, cons)
            except Exception:
                pass

    if es_principal:
        try:
            gd.setBackground(Color(240, 245, 240))
        except Exception:
            pass


# ==========================================================================
#  CONVERSIÓN DE COLOR Y UTILIDADES
# ==========================================================================

def rgb_a_cbcr(r, g, b):
    """Convierte RGB a componentes Cb y Cr del espacio YCbCr."""
    cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0
    cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0
    return cb, cr


def obtener_color_medio_roi(imp):
    """Calcula el color RGB promedio de la ROI rectangular seleccionada."""
    roi = imp.getRoi()
    if roi is None or roi.getType() != Roi.RECTANGLE:
        return None
    cp = imp.getProcessor()
    rect = roi.getBounds()
    sum_r = 0.0
    sum_g = 0.0
    sum_b = 0.0
    count = 0
    for y in range(rect.y, rect.y + rect.height):
        for x in range(rect.x, rect.x + rect.width):
            c = cp.get(x, y)
            r = (c >> 16) & 0xFF
            g = (c >> 8) & 0xFF
            b = c & 0xFF
            sum_r += r
            sum_g += g
            sum_b += b
            count += 1
    if count == 0:
        return None
    return int(sum_r / count), int(sum_g / count), int(sum_b / count)


# ==========================================================================
#  SISTEMA DE ENTRENAMIENTO
# ==========================================================================

def filtrar_por_color(imp_original, r_ref, g_ref, b_ref, radio=30):
    """
    Genera una imagen filtrada: los píxeles dentro del radio de distancia
    euclidiana en CbCr respecto al color de referencia conservan su color
    original; el resto se pone blanco (255, 255, 255).
    Usa getPixels() para velocidad óptima en Jython.
    """
    w = imp_original.getWidth()
    h = imp_original.getHeight()
    imp_filtrada = IJ.createImage("Colour Filter", "RGB", w, h, 1)
    cp_orig = imp_original.getProcessor()
    cp_filt = imp_filtrada.getProcessor()

    pixels_orig = cp_orig.getPixels()
    pixels_filt = cp_filt.getPixels()

    cb_ref, cr_ref = rgb_a_cbcr(r_ref, g_ref, b_ref)
    radio_sq = radio * radio  # comparar al cuadrado, evita sqrt
    blanco = 0x00FFFFFF  # (255 << 16) + (255 << 8) + 255

    total = w * h
    for k in range(total):
        c = pixels_orig[k] & 0xFFFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0
        cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0
        dist_sq = (cb - cb_ref) * (cb - cb_ref) + (cr - cr_ref) * (cr - cr_ref)
        if dist_sq < radio_sq:
            pixels_filt[k] = pixels_orig[k]
        else:
            pixels_filt[k] = blanco

    imp_filtrada.updateAndDraw()
    return imp_filtrada


def calcular_histogramas(imp_filtrada, imp_original):
    """
    Computa histogramas en espacio CbCr (128x128 bins) para píxeles
    positivos (no-blancos en filtrada) y negativos (blancos en filtrada,
    tomando el color de la imagen original).
    Usa getPixels() para velocidad óptima en Jython.
    """
    hist_pos = [0.0] * 16384
    hist_neg = [0.0] * 16384
    pixels_filt = imp_filtrada.getProcessor().getPixels()
    pixels_orig = imp_original.getProcessor().getPixels()
    total = imp_original.getWidth() * imp_original.getHeight()
    blanco = 0x00FFFFFF
    count_pos = 0
    count_neg = 0

    for k in range(total):
        c_filt = pixels_filt[k] & 0xFFFFFFFF
        if c_filt != blanco:
            r = (c_filt >> 16) & 0xFF
            g = (c_filt >> 8) & 0xFF
            b = c_filt & 0xFF
            cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0
            cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0
            i = int(cb / 2.0)
            j = int(cr / 2.0)
            if i < 0: i = 0
            elif i > 127: i = 127
            if j < 0: j = 0
            elif j > 127: j = 127
            n = i * 128 + j
            hist_pos[n] += 1.0
            count_pos += 1
        else:
            c_orig = pixels_orig[k] & 0xFFFFFFFF
            r = (c_orig >> 16) & 0xFF
            g = (c_orig >> 8) & 0xFF
            b = c_orig & 0xFF
            cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0
            cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0
            i = int(cb / 2.0)
            j = int(cr / 2.0)
            if i < 0: i = 0
            elif i > 127: i = 127
            if j < 0: j = 0
            elif j > 127: j = 127
            n = i * 128 + j
            hist_neg[n] += 1.0
            count_neg += 1

    return hist_pos, hist_neg, count_pos, count_neg


def entrenar_modelo(imp_inicial):
    """
    Flujo de entrenamiento completo. Soporta múltiples rondas y múltiples imágenes.
    El usuario puede seleccionar ROIs en la imagen inicial o en cualquier otra
    imagen abierta en Fiji.
    """
    global prob_brown, prob_nonbrown, modelo_cargado

    # Histogramas acumulados a lo largo de múltiples rondas
    hist_brown_acum    = [0.0] * 16384
    hist_nonbrown_acum = [0.0] * 16384
    total_brown = 0.0
    total_nonbrown = 0.0
    ronda = 0

    imp_inicial.show()

    while True:
        ronda += 1
        gd_ronda = GenericDialog("Entrenamiento - Ronda {}".format(ronda))
        gd_ronda.addMessage("1. Dibuje un RECTANGULO sobre una zona con DAB (marron) en CUALQUIER imagen.\n2. Asegurese de hacer click en esa imagen para activarla.\n3. Presione OK para procesar la muestra.")
        estilizar_dialogo(gd_ronda)
        gd_ronda.setModal(False)
        gd_ronda.showDialog()
        
        # Esperar a que el usuario presione OK o Cancele
        while not gd_ronda.wasOKed() and not gd_ronda.wasCanceled():
            time.sleep(0.1)
        
        if gd_ronda.wasCanceled():
            IJ.showMessage("Proceso finalizado", "Entrenamiento cancelado.")
            break

        # Obtener la imagen actualmente activa (puede ser otra distinta a imp_inicial)
        imp_actual = WindowManager.getCurrentImage()
        if imp_actual is None:
            IJ.showMessage("Error", "No se detecto ninguna imagen activa.")
            continue

        color_medio = obtener_color_medio_roi(imp_actual)
        if color_medio is None:
            IJ.showMessage("Error", "Debe seleccionar una ROI rectangular sobre la imagen activa.")
            continue

        r_ref, g_ref, b_ref = color_medio
        IJ.showStatus("Filtrando por color de referencia RGB({},{},{})...".format(r_ref, g_ref, b_ref))

        # Filtrar y mostrar
        imp_filtrada = filtrar_por_color(imp_actual, r_ref, g_ref, b_ref, radio=30)
        imp_filtrada.setTitle("Muestra {} - Filtro de Color".format(ronda))
        imp_filtrada.show()

        # Calcular histogramas
        hist_pos, hist_neg, cnt_pos, cnt_neg = calcular_histogramas(imp_filtrada, imp_actual)

        # Acumular
        for i in range(16384):
            hist_brown_acum[i]    += hist_pos[i]
            hist_nonbrown_acum[i] += hist_neg[i]
        total_brown    += cnt_pos
        total_nonbrown += cnt_neg

        IJ.showStatus("Ronda {}: {} pixeles positivos, {} negativos".format(ronda, cnt_pos, cnt_neg))

        # Preguntar si quiere agregar otra muestra
        gd_mas = GenericDialog("Agregar otra muestra?")
        gd_mas.addMessage(
            "Ronda {} completada.\n"
            "Pixeles positivos acumulados: {}\n"
            "Pixeles negativos acumulados: {}\n\n"
            "Presione OK para agregar otra muestra en esta u otra imagen\n"
            "o Cancel para finalizar el entrenamiento.".format(
                ronda, int(total_brown), int(total_nonbrown)))
        estilizar_dialogo(gd_mas)
        gd_mas.showDialog()

        # Cerrar imagen filtrada de esta ronda
        imp_filtrada.changes = False
        imp_filtrada.close()

        if gd_mas.wasCanceled():
            break

        # Traer la imagen actual al frente para la siguiente ronda
        imp_actual.show()
        win = imp_actual.getWindow()
        if win is not None:
            WindowManager.setCurrentWindow(win)
            win.toFront()
        imp_actual.killRoi()  # Limpiar ROI anterior

    # Normalizar a probabilidades
    if total_brown > 0 and total_nonbrown > 0:
        for i in range(16384):
            prob_brown[i]    = hist_brown_acum[i] / total_brown
            prob_nonbrown[i] = hist_nonbrown_acum[i] / total_nonbrown
        modelo_cargado = True
        IJ.showStatus("Entrenamiento completado - modelo listo")
    else:
        IJ.showMessage("Error", "No se recopilaron suficientes datos para generar el modelo.")
        return False

    # Preguntar si desea guardar
    gd_guardar = GenericDialog("Guardar modelo?")
    gd_guardar.addMessage("Desea guardar el modelo de entrenamiento?\n"
                          "Presione OK para guardar o Cancel para omitir.")
    estilizar_dialogo(gd_guardar)
    gd_guardar.showDialog()

    if not gd_guardar.wasCanceled():
        guardar_modelo_dialogo()

    return True


def guardar_modelo_dialogo():
    """Muestra diálogo para guardar el modelo y lo escribe a disco."""
    sd = SaveDialog("Guardar modelo de entrenamiento", "Entrenamiento_DAB", ".txt")
    ruta = sd.getDirectory()
    nombre = sd.getFileName()
    if ruta is None or nombre is None:
        return
    guardar_modelo(prob_brown, prob_nonbrown, os.path.join(ruta, nombre))
    IJ.showMessage("Modelo guardado", "Modelo guardado exitosamente en:\n" + os.path.join(ruta, nombre))


def guardar_modelo(prob, pronb, ruta_archivo):
    """Guarda el modelo estadístico en formato compatible con IHC_Toolbox."""
    with open(ruta_archivo, 'w') as f:
        for i in range(128):
            for j in range(128):
                idx = i * 128 + j
                f.write("{}\t{}\t{}\t{}\n".format(i, j, prob[idx], pronb[idx]))


def cargar_modelo(ruta_archivo):
    """
    Lee un archivo de entrenamiento (formato IHC_Toolbox) y
    devuelve (prob, pronb). El archivo tiene 16384 líneas:
    cb_bin  cr_bin  prob_positivo  prob_negativo
    """
    prob = [0.0] * 16384
    pronb = [0.0] * 16384
    with open(ruta_archivo, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            cb_bin = int(parts[0])
            cr_bin = int(parts[1])
            p = float(parts[2])
            np_val = float(parts[3])
            idx = cb_bin * 128 + cr_bin
            if 0 <= idx < 16384:
                prob[idx] = p
                pronb[idx] = np_val
    return prob, pronb


def cargar_modelo_dialogo(_event=None):
    """Diálogo para seleccionar y cargar un archivo de entrenamiento existente."""
    global prob_brown, prob_nonbrown, modelo_cargado

    od = OpenDialog("Seleccionar archivo de entrenamiento (.txt)")
    ruta = od.getPath()
    if ruta is None:
        return False

    try:
        prob_brown, prob_nonbrown = cargar_modelo(ruta)
        modelo_cargado = True
        IJ.showStatus("Modelo cargado desde: " + ruta)
        IJ.showMessage("Modelo cargado", "Modelo cargado exitosamente desde:\n" + ruta)
        return True
    except Exception as e:
        IJ.showMessage("Error", "No se pudo cargar el modelo:\n{}".format(e))
        return False


# ==========================================================================
#  DETECCIÓN DE DAB Y MEDICIÓN
# ==========================================================================

def detectar_dab(imp, prob, pronb):
    """
    Clasifica cada píxel como DAB-positivo o negativo según el modelo
    estadístico. Replica la lógica de ModelFilter de IHC_Toolbox.
    Usa getPixels() para velocidad óptima en Jython y una tabla de
    búsqueda (LUT) precalculada para evitar cálculos lentos por píxel.
    """
    # Precalcular LUT (Look-Up Table) de 16384 booleanos
    is_dab_lut = [False] * 16384
    for n in range(16384):
        p = prob[n]
        pn = pronb[n]
        if p != 0.0 and pn == 0.0:
            is_dab_lut[n] = True
        elif pn != 0.0 and (p / pn) >= 0.7:
            is_dab_lut[n] = True

    w = imp.getWidth()
    h = imp.getHeight()
    imp_result = IJ.createImage("Deteccion DAB", "RGB", w, h, 1)
    pixels_orig = imp.getProcessor().getPixels()
    pixels_res  = imp_result.getProcessor().getPixels()

    blanco = 0x00FFFFFF
    count_positivo = 0
    total = w * h

    for k in range(total):
        c = pixels_orig[k] & 0xFFFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF

        cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0
        cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0
        
        # Casting rápido y clamping
        i_cb = int(cb / 2.0)
        j_cr = int(cr / 2.0)
        if i_cb < 0: i_cb = 0
        elif i_cb > 127: i_cb = 127
        if j_cr < 0: j_cr = 0
        elif j_cr > 127: j_cr = 127
        
        n = i_cb * 128 + j_cr

        if is_dab_lut[n]:
            pixels_res[k] = pixels_orig[k]
            count_positivo += 1
        else:
            pixels_res[k] = blanco

    imp_result.updateAndDraw()
    return imp_result, count_positivo


# ==== FUNCIONES DE MEDICIÓN (misma lógica que el macro original) ====

def agregar_etiquetas(rt, nombre, imagen):
    """Agrega etiquetas Nombre e Imagen a la última fila de la tabla."""
    idx = rt.size() - 1
    rt.setValue("Nombre", idx, nombre)
    rt.setValue("Imagen", idx, imagen)


def medir_area_total(imp, rt, filename):
    """
    Mide el area total del tejido excluyendo los vacíos (fondo blanco).
    Utiliza un método adaptativo (White Balance + Otsu Top 20%):
      1. Normaliza la iluminación usando el percentil 99.5 de cada canal.
      2. Filtra el top 20% más brillante de la imagen normalizada.
      3. Encuentra automáticamente el umbral de blanco mediante Otsu.
    De esta forma, la medición de área es completamente consistente sin
    importar los cambios de iluminación en el microscopio.
    """
    w = imp.getWidth()
    h = imp.getHeight()
    total_pixels = w * h
    
    cp = imp.getProcessor()
    pixels = cp.getPixels()
    
    # 1. Histogramas por canal para White Balance
    hist_r = [0]*256
    hist_g = [0]*256
    hist_b = [0]*256
    
    for k in range(total_pixels):
        c = pixels[k] & 0xFFFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        hist_r[r] += 1
        hist_g[g] += 1
        hist_b[b] += 1
        
    def get_percentile(hist, p_target):
        target_count = total_pixels * p_target
        cum = 0
        for i in range(256):
            cum += hist[i]
            if cum >= target_count:
                return i
        return 255
        
    p995_r = get_percentile(hist_r, 0.995)
    p995_g = get_percentile(hist_g, 0.995)
    p995_b = get_percentile(hist_b, 0.995)
    
    scale_r = 255.0 / float(p995_r) if p995_r > 10 else 1.0
    scale_g = 255.0 / float(p995_g) if p995_g > 10 else 1.0
    scale_b = 255.0 / float(p995_b) if p995_b > 10 else 1.0
    
    # 2. Histograma del min(R,G,B) normalizado
    min_hist = [0]*256
    for k in range(total_pixels):
        c = pixels[k] & 0xFFFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        
        r_wb = int(r * scale_r)
        g_wb = int(g * scale_g)
        b_wb = int(b * scale_b)
        if r_wb > 255: r_wb = 255
        if g_wb > 255: g_wb = 255
        if b_wb > 255: b_wb = 255
        
        min_val = min(r_wb, g_wb, b_wb)
        min_hist[min_val] += 1
        
    # 3. Percentil 80 del min_hist
    p80_val = get_percentile(min_hist, 0.80)
    
    # 4. Otsu sobre el top 20% más brillante
    total_top = 0
    sum_top = 0.0
    for i in range(p80_val + 1, 256):
        total_top += min_hist[i]
        sum_top += i * min_hist[i]
        
    if total_top == 0:
        threshold = 240
    else:
        sumB = 0.0
        wB = 0
        wF = 0
        varMax = 0.0
        threshold = p80_val
        
        for i in range(p80_val + 1, 256):
            wB += min_hist[i]
            if wB == 0:
                continue
            wF = total_top - wB
            if wF == 0:
                break
            
            sumB += float(i * min_hist[i])
            mB = sumB / float(wB)
            mF = (sum_top - sumB) / float(wF)
            
            varBetween = float(wB) * float(wF) * (mB - mF) * (mB - mF)
            if varBetween > varMax:
                varMax = varBetween
                threshold = i

    # Fallback si el umbral es demasiado bajo
    if threshold < 200:
        threshold = 240

    # 5. Crear la máscara de tejido
    from ij.process import ByteProcessor
    mask_pixels = jarray.zeros(total_pixels, 'b')
    for k in range(total_pixels):
        c = pixels[k] & 0xFFFFFFFF
        r = (c >> 16) & 0xFF
        g = (c >> 8) & 0xFF
        b = c & 0xFF
        
        r_wb = int(r * scale_r)
        if r_wb > 255: r_wb = 255
        g_wb = int(g * scale_g)
        if g_wb > 255: g_wb = 255
        b_wb = int(b * scale_b)
        if b_wb > 255: b_wb = 255
        
        if min(r_wb, g_wb, b_wb) <= threshold:
            mask_pixels[k] = -1 # 255 en unsigned byte (Tejido)
        else:
            mask_pixels[k] = 0  # 0 (Fondo)
            
    bp = ByteProcessor(w, h, mask_pixels, None)
    
    # 6. Limpieza morfológica suave (Close y Open)
    for _ in range(2): bp.dilate()
    for _ in range(2): bp.erode()
    for _ in range(2): bp.erode()
    for _ in range(2): bp.dilate()

    imp_mask = ImagePlus("Area Total Mask", bp)
    imp_mask.show()
    WindowManager.setCurrentWindow(imp_mask.getWindow())
    
    from ij.process import ImageProcessor
    imp_mask.getProcessor().setThreshold(1, 255, ImageProcessor.NO_LUT_UPDATE)
    IJ.run(imp_mask, "Measure", "")
    
    agregar_etiquetas(rt, "Area Total", filename)
    imp_mask.changes = False
    imp_mask.close()


def medir_intensidad_dab(imp_dab, rt, filename):
    """Mide area e intensidad del DAB asumiendo que el fondo ya es blanco puro."""
    imp_dab.show()
    WindowManager.setCurrentWindow(imp_dab.getWindow())
    
    IJ.run("RGB Stack")
    IJ.run("Duplicate...", "duplicate range=2-2 use") # Canal Verde
    imp_canal = IJ.getImage()
    
    # Al invertir, el fondo blanco (255) pasa a ser negro absoluto (0)
    # y el DAB pasa a tener magnitud > 0
    IJ.run(imp_canal, "Invert", "")
    IJ.run(imp_canal, "8-bit", "")
    
    from ij.process import ImageProcessor
    # Umbral ABSOLUTO: Medir todo lo que no sea fondo (1 a 255)
    imp_canal.getProcessor().setThreshold(1, 255, ImageProcessor.NO_LUT_UPDATE)
    
    IJ.run(imp_canal, "Measure", "")
    agregar_etiquetas(rt, "Area e Intensidad de DAB", filename)
    
    imp_canal.changes = False
    imp_canal.close()


# ==========================================================================
#  RENOMBRAR ARCHIVOS
# ==========================================================================

def renombrar_archivos(root_dir):
    for foldername, _, filenames in os.walk(root_dir):
        subfolder = os.path.basename(foldername)
        if not subfolder:
            continue
        for fname in filenames:
            if not fname.lower().endswith(".tif"):
                continue
            if fname.startswith(subfolder + "_"):
                continue
            old_path = os.path.join(foldername, fname)
            new_name = subfolder + "_" + fname
            new_path = os.path.join(foldername, new_name)
            try:
                os.rename(old_path, new_path)
            except Exception:
                pass


# ==========================================================================
#  VENTANA DE CONFIGURACION INICIAL
# ==========================================================================

def solicitar_entrenamiento(_event=None):
    """Cierra el diálogo principal y activa la bandera para entrenamiento."""
    global ir_a_entrenar
    ir_a_entrenar = True
    try:
        source = _event.getSource()
        parent = source.getParent()
        while parent is not None:
            if isinstance(parent, GenericDialog):
                parent.dispose()
                break
            parent = parent.getParent()
    except Exception:
        pass


def mostrar_ventana_configuracion():

    global ir_a_calibrar, ir_a_entrenar, modelo_cargado
    ir_a_calibrar = False
    ir_a_entrenar = False

    gd = GenericDialog("Analizar INTENSIDAD de DAB")

    gd.addMessage("INFORMACIÓN")

    # Panel superior: INFO DEL PLUGIN + GUIA DE USO
    panel_botones_sup = Panel()
    panel_botones_sup.setLayout(GridLayout(1, 2, 5, 0))
    btn_info = Button("ACERCA DEL PLUGIN")
    btn_guia = Button(u"GU\u00cdA DE USO")
    btn_info.addActionListener(mostrar_info_plugin)
    btn_guia.addActionListener(abrir_guia)
    panel_botones_sup.add(btn_info)
    panel_botones_sup.add(btn_guia)
    gd.addPanel(panel_botones_sup)

    # Sección: CALIBRACION
    gd.addMessage("CALIBRACIÓN")

    panel_botones_inf = Panel()
    panel_botones_inf.setLayout(GridLayout(1, 2, 5, 0))
    btn_manual   = Button(u"GU\u00cdA DE CALIBRACIÓN")
    btn_calibrar = Button("CALIBRAR")
    btn_manual.addActionListener(abrir_ayuda)
    btn_calibrar.addActionListener(abrir_calibracion)
    panel_botones_inf.add(btn_manual)
    panel_botones_inf.add(btn_calibrar)
    gd.addPanel(panel_botones_inf)

    # Sección: ENTRENAMIENTO DAB
    gd.addMessage("ENTRENAMIENTO DAB")

    panel_botones_dab = Panel()
    panel_botones_dab.setLayout(GridLayout(1, 2, 5, 0))
    btn_entrenar = Button("ENTRENAR SISTEMA")
    btn_cargar   = Button("CARGAR ENTRENAMIENTO")
    btn_entrenar.addActionListener(solicitar_entrenamiento)
    btn_cargar.addActionListener(cargar_modelo_dialogo)
    panel_botones_dab.add(btn_entrenar)
    panel_botones_dab.add(btn_cargar)
    gd.addPanel(panel_botones_dab)

    # Aplicar estilos
    estilizar_dialogo(gd, es_principal=True,
                      btn_info=btn_info, btn_guia=btn_guia,
                      btn_manual=btn_manual, btn_calibrar=btn_calibrar,
                      btn_entrenar=btn_entrenar, btn_cargar=btn_cargar)

    gd.showDialog()

    # Primero chequear los botones de salto para que "wasCanceled" no rompa la navegación
    if ir_a_entrenar:
        return "entrenar"
    
    if ir_a_calibrar:
        return "calibrar"

    if gd.wasCanceled():
        return None

    # Verificar que hay modelo cargado
    if not modelo_cargado:
        IJ.showMessage("Error",
                       "Debe entrenar o cargar un modelo antes de continuar.\n"
                       "Use los botones 'ENTRENAR SISTEMA' o 'CARGAR ENTRENAMIENTO'.")
        return None

    return {}


# ==========================================================================
#  FUNCION PRINCIPAL: PROCESAR CARPETA
# ==========================================================================

def procesar_carpeta(root_dir, opciones):

    # Configurar mediciones (misma config que el macro original)
    IJ.run("Set Measurements...", "area mean standard stack limit display redirect=None decimal=2")
    rt = ResultsTable.getResultsTable()
    rt.reset()  # CORRECCIÓN: resetear la tabla para que no acumule datos de carpetas previas
    count = 0

    # Listar imágenes
    extensiones = (".tif", ".jpg", ".png")

    for foldername, _, filenames in os.walk(root_dir):
        for fname in sorted(filenames):
            if not fname.lower().endswith(extensiones):
                continue

            filepath = os.path.join(foldername, fname)
            imp = IJ.openImage(filepath)
            if imp is None:
                print("No se pudo abrir: " + fname)
                continue

            IJ.showStatus("Procesando: " + fname)
            imp.show()


            # a) Detectar DAB con el modelo (toma unos segundos)
            imp_dab, cnt_pos = detectar_dab(imp, prob_brown, prob_nonbrown)
            imp_dab.setTitle("Deteccion DAB - " + fname)

            # b) Medir área total (esto abre la ventana Results inmediatamente)
            medir_area_total(imp, rt, fname)

            # c) Medir intensidad DAB sobre la imagen filtrada
            medir_intensidad_dab(imp_dab, rt, fname)

            count += 1

            # Cerrar imágenes y continuar automáticamente
            imp_dab.changes = False
            imp_dab.close()
            imp.changes = False
            imp.close()
            IJ.run("Close All")

    # Guardar como Excel (.xlsx) usando Apache POI (incluido en el JAR)
    if rt and rt.size() > 0:
        columnas = ["Imagen", "Parametro", "Area", "Intensidad", "StdDev"]
        from org.apache.poi.xssf.usermodel import XSSFWorkbook
        from java.io import FileOutputStream

        folder_name = os.path.basename(root_dir.rstrip(os.sep))
        output_name = "Resultados_DAB_{}.xlsx".format(folder_name)
        output_path = os.path.join(root_dir, output_name)
        wb = XSSFWorkbook()
        sheet = wb.createSheet("Resultados DAB")

        # Encabezados
        header_row = sheet.createRow(0)
        for col_idx in range(len(columnas)):
            header_row.createCell(col_idx).setCellValue(columnas[col_idx])

        # Datos
        for i in range(rt.size()):
            row = sheet.createRow(i + 1)
            row.createCell(0).setCellValue(rt.getStringValue("Imagen", i))
            row.createCell(1).setCellValue(rt.getStringValue("Nombre", i))
            row.createCell(2).setCellValue(rt.getValue("Area", i))
            row.createCell(3).setCellValue(rt.getValue("Mean", i))
            row.createCell(4).setCellValue(rt.getValue("StdDev", i))

        # Auto-ajustar ancho de columnas
        for col_idx in range(len(columnas)):
            sheet.autoSizeColumn(col_idx)

        fos = FileOutputStream(output_path)
        wb.write(fos)
        fos.close()
        wb.close()

    # Cerrar ventana Results
    for win in WindowManager.getNonImageWindows():
        if isinstance(win, TextWindow) and win.getTitle() == "Results":
            win.setVisible(False)
            win.close(False)

    # Cartel de éxito
    IJ.showMessage("Proceso completado",
                   "Se analizaron {} fotos.\nResultados guardados en: {}".format(count, output_name))


    return True


# ==========================================================================
#  PUNTO DE ENTRADA — FIJI ejecuta el script desde aqui
# ==========================================================================
continuar = True
while continuar:
    # 1. Ventana de configuración
    opciones = mostrar_ventana_configuracion()
    if opciones is None:
        break

    # 2. Entrenamiento (si el usuario lo solicitó desde la ventana inicial)
    if opciones == "entrenar":
        od = OpenDialog("Abra una imagen para entrenar el modelo DAB")
        ruta = od.getPath()
        if ruta is not None:
            imp_train = IJ.openImage(ruta)
            if imp_train is not None:
                entrenar_modelo(imp_train)
                imp_train.changes = False
                imp_train.close()
                IJ.run("Close All")
        continue  # Volver a mostrar la ventana de configuración

    # 3. Calibración (si el usuario la solicitó desde la ventana inicial)
    if opciones == "calibrar" or ir_a_calibrar:
        gd_cal = GenericDialog("Calibrar imagen")
        gd_cal.addMessage("1. Abra una imagen y calibre desde SET SCALE.\n"
                          "2. Cierre la imagen sin guardar (DON'T SAVE).\n"
                          "3. Presione OK para continuar.")
        estilizar_dialogo(gd_cal)
        gd_cal.setModal(False)
        gd_cal.showDialog()
        
        while not gd_cal.wasOKed() and not gd_cal.wasCanceled():
            IJ.wait(100)
            
        if gd_cal.wasCanceled():
            IJ.showMessage("Proceso finalizado", "Calibracion y proceso cancelados.")
            break
        
        continue

    # 4. Seleccionar carpeta
    dc = DirectoryChooser("Selecciona la carpeta con las imagenes DAB a analizar")
    selected_path = dc.getDirectory()
    if not selected_path:
        break

    # 5. Renombrar archivos .tif (agrega nombre de subcarpeta como prefijo)
    renombrar_archivos(selected_path)

    # 6. Procesar
    if not procesar_carpeta(selected_path, opciones):
        break

    # 7. ¿Otra carpeta?
    gd_rep = GenericDialog("Analizar otra carpeta")
    gd_rep.addMessage("Presiona OK para seleccionar otra carpeta o Cancelar para salir.")
    estilizar_dialogo(gd_rep)
    gd_rep.showDialog()
    continuar = not gd_rep.wasCanceled()
