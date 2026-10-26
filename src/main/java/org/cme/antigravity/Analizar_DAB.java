package org.cme.antigravity;

import ij.IJ;
import ij.ImagePlus;
import ij.WindowManager;
import ij.io.DirectoryChooser;
import ij.gui.GenericDialog;
import ij.gui.Roi;
import ij.io.OpenDialog;
import ij.io.SaveDialog;
import ij.measure.ResultsTable;
import ij.plugin.PlugIn;
import ij.process.ImageProcessor;

import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.ss.usermodel.Row;

import java.awt.Button;
import java.awt.Color;
import java.awt.Component;
import java.awt.Font;
import java.awt.GridLayout;
import java.awt.Panel;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.FilenameFilter;
import java.util.Arrays;

public class Analizar_DAB implements PlugIn {

    private double[] prob_brown = new double[16384];
    private double[] prob_nonbrown = new double[16384];
    private boolean modelo_cargado = false;
    private boolean ir_a_calibrar = false;
    private boolean ir_a_entrenar = false;

    private final Color color_blanco = new Color(255, 255, 255);
    private final Color color_manual = new Color(157, 167, 159);
    private final Color color_calibrar = new Color(25, 136, 255);
    private final Color color_info = new Color(0, 151, 161);
    private final Color color_dab = new Color(139, 69, 19);

    @Override
    public void run(String arg) {
        boolean continuar = true;
        while (continuar) {
            String opciones = mostrarVentanaConfiguracion();
            if (opciones == null) {
                // Interrupcion: el usuario cancelo la ventana de configuracion.
                IJ.showMessage("Proceso finalizado", "PROCESO DETENIDO");
                break;
            }

            // Falta el modelo de entrenamiento: ya se aviso con un cartel, y volvemos a
            // la ventana de configuracion en vez de cerrar el plugin.
            if (opciones.equals("reintentar"))
                continue;

            if (opciones.equals("entrenar")) {
                OpenDialog od = new OpenDialog("Abra una imagen para entrenar el modelo DAB", "");
                String dir = od.getDirectory();
                String name = od.getFileName();
                if (dir != null && name != null) {
                    ImagePlus imp_train = IJ.openImage(dir + name);
                    if (imp_train != null) {
                        entrenarModelo(imp_train);
                        imp_train.changes = false;
                        imp_train.close();
                        IJ.run("Close All");
                    }
                }
                continue;
            }

            if (ir_a_calibrar) {
                GenericDialog gd_cal = new GenericDialog("Calibrar imagen");
                gd_cal.addMessage("1. Abra una imagen y calibre desde SET SCALE.\n" +
                        "2. Cierre la imagen sin guardar (DON'T SAVE).\n" +
                        "3. Presione OK para continuar.");
                estilizarDialogo(gd_cal, false);
                gd_cal.setModal(false);
                gd_cal.showDialog();
                while (!gd_cal.wasOKed() && !gd_cal.wasCanceled()) {
                    IJ.wait(100);
                }
                if (gd_cal.wasCanceled()) {
                    // Interrupcion: el usuario cancelo la calibracion.
                    IJ.showMessage("Proceso finalizado", "PROCESO DETENIDO");
                    break;
                }
                continue;
            }

            DirectoryChooser dc = new DirectoryChooser("Selecciona la carpeta con las imagenes DAB a analizar");
            String selectedPath = dc.getDirectory();
            if (selectedPath == null || selectedPath.isEmpty()) {
                // Interrupcion: el usuario cancelo el selector de carpeta.
                IJ.showMessage("Proceso finalizado", "PROCESO DETENIDO");
                break;
            }

            renombrarArchivos(new File(selectedPath));

            if (!procesarCarpeta(new File(selectedPath))) {
                // Interrupcion: el analisis de la carpeta no llego a completarse.
                IJ.showMessage("Proceso finalizado", "PROCESO DETENIDO");
                break;
            }

            GenericDialog gd_rep = new GenericDialog("Analizar otra carpeta");
            gd_rep.addMessage("Presiona OK para seleccionar otra carpeta o Cancelar para salir.");
            estilizarDialogo(gd_rep, false);
            gd_rep.showDialog();
            // Salida normal: cancelar aca significa que el usuario termino de trabajar,
            // no es una interrupcion. Por eso el bucle termina en silencio, sin cartel de
            // "PROCESO DETENIDO" (ese queda reservado para los cortes de arriba).
            continuar = !gd_rep.wasCanceled();
        }
    }

    private String mostrarVentanaConfiguracion() {
        ir_a_calibrar = false;
        ir_a_entrenar = false;

        GenericDialog gd = new GenericDialog("Analizar INTENSIDAD de DAB");

        gd.addMessage("INFORMACIÓN");

        Panel panel_botones_sup = new Panel();
        panel_botones_sup.setLayout(new GridLayout(1, 2, 5, 0));
        Button btn_info = new Button("ACERCA DEL PLUGIN");
        Button btn_guia = new Button("GU\u00cdA DE USO");
        btn_info.addActionListener(e -> mostrarInfoPlugin());
        btn_guia.addActionListener(e -> abrirGuia());
        panel_botones_sup.add(btn_info);
        panel_botones_sup.add(btn_guia);
        gd.addPanel(panel_botones_sup);

        gd.addMessage("CALIBRACIÓN");

        Panel panel_botones_inf = new Panel();
        panel_botones_inf.setLayout(new GridLayout(1, 2, 5, 0));
        Button btn_manual = new Button("GU\u00cdA DE CALIBRACI\u00d3N");
        Button btn_calibrar = new Button("CALIBRAR");
        btn_manual.addActionListener(e -> abrirAyuda());
        btn_calibrar.addActionListener(e -> abrirCalibracion((Component) e.getSource()));
        panel_botones_inf.add(btn_manual);
        panel_botones_inf.add(btn_calibrar);
        gd.addPanel(panel_botones_inf);

        gd.addMessage("ENTRENAMIENTO DAB");

        Panel panel_botones_dab = new Panel();
        panel_botones_dab.setLayout(new GridLayout(1, 2, 5, 0));
        Button btn_entrenar = new Button("ENTRENAR SISTEMA");
        Button btn_cargar = new Button("CARGAR ENTRENAMIENTO");
        btn_entrenar.addActionListener(e -> solicitarEntrenamiento((Component) e.getSource()));
        btn_cargar.addActionListener(e -> cargarModeloDialog());
        panel_botones_dab.add(btn_entrenar);
        panel_botones_dab.add(btn_cargar);
        gd.addPanel(panel_botones_dab);

        estilizarDialogo(gd, true, btn_info, btn_guia, btn_manual, btn_calibrar, btn_entrenar, btn_cargar);

        gd.showDialog();

        if (ir_a_entrenar)
            return "entrenar";
        if (ir_a_calibrar)
            return "calibrar";
        if (gd.wasCanceled())
            return null;
        if (!modelo_cargado) {
            IJ.showMessage("Error",
                    "Debe entrenar o cargar un modelo antes de continuar.\nUse los botones 'ENTRENAR SISTEMA' o 'CARGAR ENTRENAMIENTO'.");
            // OJO: no devolver null. null significa "el usuario cancelo" y cierra el
            // plugin. Aca solo falta el modelo, asi que volvemos a la configuracion.
            return "reintentar";
        }

        return "procesar";
    }

    private void solicitarEntrenamiento(Component source) {
        ir_a_entrenar = true;
        cerrarDialogoPadre(source);
    }

    private void abrirCalibracion(Component source) {
        ir_a_calibrar = true;
        cerrarDialogoPadre(source);
    }

    private void cerrarDialogoPadre(Component source) {
        try {
            Component parent = source.getParent();
            while (parent != null) {
                if (parent instanceof GenericDialog) {
                    ((GenericDialog) parent).dispose();
                    break;
                }
                parent = parent.getParent();
            }
        } catch (Exception ignored) {
        }
    }

    private void estilizarDialogo(GenericDialog gd, boolean esPrincipal, Button... botones) {
        Font font_msg = new Font("SansSerif", Font.PLAIN, 12);
        Font font_btn = new Font("SansSerif", Font.PLAIN, 10);
        Font font_btn1 = new Font("SansSerif", Font.BOLD, 10);
        Font font_section = new Font("SansSerif", Font.BOLD, 13);

        if (botones.length >= 2) {
            if (botones[0] != null) {
                botones[0].setFont(font_btn);
                botones[0].setForeground(Color.WHITE);
                botones[0].setBackground(color_info);
            }
            if (botones[1] != null) {
                botones[1].setFont(font_btn);
                botones[1].setForeground(Color.WHITE);
                botones[1].setBackground(color_info);
            }
        }
        if (botones.length >= 4) {
            if (botones[2] != null) {
                botones[2].setFont(font_btn);
                botones[2].setForeground(Color.WHITE);
                botones[2].setBackground(color_manual);
            }
            if (botones[3] != null) {
                botones[3].setFont(font_btn);
                botones[3].setForeground(Color.WHITE);
                botones[3].setBackground(color_manual);
            }
        }
        if (botones.length >= 6) {
            if (botones[4] != null) {
                botones[4].setFont(font_btn1);
                botones[4].setForeground(Color.WHITE);
                botones[4].setBackground(color_dab);
            }
            if (botones[5] != null) {
                botones[5].setFont(font_btn1);
                botones[5].setForeground(Color.WHITE);
                botones[5].setBackground(color_dab);
            }
        }

        java.awt.GridBagLayout layout = null;
        if (gd.getLayout() instanceof java.awt.GridBagLayout) {
            layout = (java.awt.GridBagLayout) gd.getLayout();
        }

        for (Component comp : gd.getComponents()) {
            if (comp instanceof java.awt.Label) {
                String text = ((java.awt.Label) comp).getText();
                boolean esMensaje = text.contains(":") || text.contains("Presiona");
                boolean esSeccion = text.equals("INFORMACIÓN") || text.equals("ENTRENAMIENTO DAB")
                        || text.equals("CALIBRACIÓN")
                        || text.equals("MEDICION DE AREA");

                if (esMensaje) {
                    comp.setFont(font_msg);
                    comp.setForeground(new Color(50, 50, 50));
                } else if (esSeccion) {
                    comp.setFont(font_section);
                    comp.setBackground(color_calibrar);
                    comp.setForeground(color_blanco);
                    ((java.awt.Label) comp).setAlignment(java.awt.Label.CENTER);

                    if (layout != null) {
                        java.awt.GridBagConstraints cons = layout.getConstraints(comp);
                        if (cons != null) {
                            cons.fill = java.awt.GridBagConstraints.HORIZONTAL; // 2
                            cons.insets = new java.awt.Insets(cons.insets.top, 10, cons.insets.bottom, 10);
                            layout.setConstraints(comp, cons);
                        }
                    }
                } else {
                    comp.setFont(font_msg);
                }
            } else if (comp instanceof java.awt.Panel) {
                if (layout != null) {
                    java.awt.GridBagConstraints cons = layout.getConstraints(comp);
                    if (cons != null) {
                        cons.fill = java.awt.GridBagConstraints.HORIZONTAL; // 2
                        cons.insets = new java.awt.Insets(cons.insets.top, 10, cons.insets.bottom, 10);
                        layout.setConstraints(comp, cons);
                    }
                }
            }
        }
    }

    private void mostrarInfoPlugin() {
        GenericDialog gd = new GenericDialog("Informacion del Plugin");
        try {
            java.net.URL url = getClass().getResource("/Analizar DAB logo design-Final.png");
            if (url != null) {
                java.awt.image.BufferedImage img = javax.imageio.ImageIO.read(url);
                if (img != null) {
                    int w = 300;
                    int h = (int)(((double)img.getHeight() / img.getWidth()) * w);
                    java.awt.Image scaledImg = img.getScaledInstance(w, h, java.awt.Image.SCALE_SMOOTH);
                    gd.addImage(new ImagePlus("Logo", scaledImg));
                }
            }
        } catch (Exception e) {
            // Ignorar errores de carga de imagen para que el plugin siga funcionando
        }

        String infoTexto = "<html><center><br><h3>Analizar DAB</h3>Analisis Cuantitativo de Inmunohistoquimicas.<br><br><b>Creado por:</b><br><b>Dr. Ezequiel Grondona</b><br>-UNC - INICSA - CONICET-<br>- 2026 -<br><br>Lea atentamente la guia de uso antes de utilizar el plugin.<br>Consultas y sugerencias:<br>ezequiel.grondona@unc.edu.ar<br></center></html>";
        Panel panel = new Panel();
        javax.swing.JLabel label = new javax.swing.JLabel(infoTexto);
        panel.add(label);
        gd.addPanel(panel);
        
        estilizarDialogo(gd, false);
        gd.showDialog();
    }

    // Las guias se abren con la ruta "blob" del repositorio, no con
    // "raw": con "raw" el navegador fuerza la descarga del PDF, con
    // "blob" GitHub lo muestra en su visor y el usuario lo lee ahi
    // mismo.
    //
    // Estos enlaces viven dentro del binario, de modo que el plugin
    // ya instalado depende de que la ruta siga existiendo. Si alguna
    // vez se mueve el repositorio, hay que cambiarlos aca y publicar
    // una version nueva: no alcanza con mover los archivos.
    private void abrirGuia() {
        try {
            java.awt.Desktop.getDesktop().browse(new java.net.URI(
                    "https://github.com/ezegrondona/Analizar-DAB/blob/main/docs/Gu%C3%ADa%20de%20Uso%20-%20Analizar%20DAB.pdf"));
        } catch (Exception e) {
            IJ.showMessage("Error", "No se pudo abrir el enlace:\n" + e.getMessage());
        }
    }

    private void abrirAyuda() {
        try {
            java.awt.Desktop.getDesktop().browse(new java.net.URI(
                    "https://github.com/ezegrondona/Analizar-DAB/blob/main/docs/Gu%C3%ADa%20de%20Calibraci%C3%B3n%20FIJI-ImajeJ.pdf"));
        } catch (Exception e) {
            IJ.showMessage("Error", "No se pudo abrir el enlace:\n" + e.getMessage());
        }
    }

    private double[] rgbACbcr(int r, int g, int b) {
        double cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0;
        double cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0;
        return new double[] { cb, cr };
    }

    private int[] obtenerColorMedioRoi(ImagePlus imp) {
        Roi roi = imp.getRoi();
        if (roi == null || roi.getType() != Roi.RECTANGLE)
            return null;
        ImageProcessor cp = imp.getProcessor();
        java.awt.Rectangle rect = roi.getBounds();
        long sum_r = 0, sum_g = 0, sum_b = 0, count = 0;
        for (int y = rect.y; y < rect.y + rect.height; y++) {
            for (int x = rect.x; x < rect.x + rect.width; x++) {
                int c = cp.getPixel(x, y);
                int r = (c >> 16) & 0xFF;
                int g = (c >> 8) & 0xFF;
                int b = c & 0xFF;
                sum_r += r;
                sum_g += g;
                sum_b += b;
                count++;
            }
        }
        if (count == 0)
            return null;
        return new int[] { (int) (sum_r / count), (int) (sum_g / count), (int) (sum_b / count) };
    }

    private ImagePlus filtrarPorColor(ImagePlus impOriginal, int rRef, int gRef, int bRef, int radio) {
        int w = impOriginal.getWidth();
        int h = impOriginal.getHeight();
        ImagePlus impFiltrada = IJ.createImage("Colour Filter", "RGB", w, h, 1);
        ImageProcessor cpOrig = impOriginal.getProcessor();
        ImageProcessor cpFilt = impFiltrada.getProcessor();
        int[] pixelsOrig = (int[]) cpOrig.getPixels();
        int[] pixelsFilt = (int[]) cpFilt.getPixels();
        double[] refCbCr = rgbACbcr(rRef, gRef, bRef);
        double cbRef = refCbCr[0], crRef = refCbCr[1];
        int radioSq = radio * radio, blanco = 0x00FFFFFF, total = w * h;

        for (int k = 0; k < total; k++) {
            int c = pixelsOrig[k];
            int r = (c >> 16) & 0xFF;
            int g = (c >> 8) & 0xFF;
            int b = c & 0xFF;
            double cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0;
            double cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0;
            double distSq = (cb - cbRef) * (cb - cbRef) + (cr - crRef) * (cr - crRef);
            if (distSq < radioSq)
                pixelsFilt[k] = pixelsOrig[k];
            else
                pixelsFilt[k] = blanco;
        }
        impFiltrada.updateAndDraw();
        return impFiltrada;
    }

    private class HistResult {
        double[] histPos = new double[16384];
        double[] histNeg = new double[16384];
        long countPos = 0, countNeg = 0;
    }

    private HistResult calcularHistogramas(ImagePlus impFiltrada, ImagePlus impOriginal) {
        HistResult result = new HistResult();
        int[] pixelsFilt = (int[]) impFiltrada.getProcessor().getPixels();
        int[] pixelsOrig = (int[]) impOriginal.getProcessor().getPixels();
        int total = impOriginal.getWidth() * impOriginal.getHeight();
        int blanco = 0x00FFFFFF;

        for (int k = 0; k < total; k++) {
            int cFilt = pixelsFilt[k] & 0x00FFFFFF;
            if (cFilt != blanco) {
                int r = (pixelsFilt[k] >> 16) & 0xFF;
                int g = (pixelsFilt[k] >> 8) & 0xFF;
                int b = pixelsFilt[k] & 0xFF;
                double cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0;
                double cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0;
                int i = (int) Math.max(0, Math.min(127, cb / 2.0));
                int j = (int) Math.max(0, Math.min(127, cr / 2.0));
                result.histPos[i * 128 + j]++;
                result.countPos++;
            } else {
                int cOrig = pixelsOrig[k];
                int r = (cOrig >> 16) & 0xFF;
                int g = (cOrig >> 8) & 0xFF;
                int b = cOrig & 0xFF;
                double cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0;
                double cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0;
                int i = (int) Math.max(0, Math.min(127, cb / 2.0));
                int j = (int) Math.max(0, Math.min(127, cr / 2.0));
                result.histNeg[i * 128 + j]++;
                result.countNeg++;
            }
        }
        return result;
    }

    private void entrenarModelo(ImagePlus impInicial) {
        double[] hist_brown_acum = new double[16384];
        double[] hist_nonbrown_acum = new double[16384];
        long total_brown = 0, total_nonbrown = 0;
        int ronda = 0;

        impInicial.show();
        while (true) {
            ronda++;
            GenericDialog gd_ronda = new GenericDialog("Entrenamiento - Ronda " + ronda);
            gd_ronda.addMessage(
                    "1. Dibuje un RECTANGULO sobre una zona con DAB (marron) en CUALQUIER imagen.\n2. Asegurese de hacer click en esa imagen para activarla.\n3. Presione OK para procesar la muestra.");
            estilizarDialogo(gd_ronda, false);
            gd_ronda.setModal(false);
            gd_ronda.showDialog();
            while (!gd_ronda.wasOKed() && !gd_ronda.wasCanceled()) {
                IJ.wait(100);
            }
            if (gd_ronda.wasCanceled()) {
                IJ.showMessage("Proceso finalizado", "Entrenamiento cancelado.");
                break;
            }
            ImagePlus impActual = WindowManager.getCurrentImage();
            if (impActual == null) {
                IJ.showMessage("Error", "No se detecto ninguna imagen activa.");
                continue;
            }
            int[] colorMedio = obtenerColorMedioRoi(impActual);
            if (colorMedio == null) {
                IJ.showMessage("Error", "Debe seleccionar una ROI rectangular sobre la imagen activa.");
                continue;
            }
            int rRef = colorMedio[0], gRef = colorMedio[1], bRef = colorMedio[2];
            IJ.showStatus(String.format("Filtrando por color de referencia RGB(%d,%d,%d)...", rRef, gRef, bRef));
            ImagePlus impFiltrada = filtrarPorColor(impActual, rRef, gRef, bRef, 30);
            impFiltrada.setTitle("Muestra " + ronda + " - Filtro de Color");
            impFiltrada.show();
            HistResult calc = calcularHistogramas(impFiltrada, impActual);
            for (int i = 0; i < 16384; i++) {
                hist_brown_acum[i] += calc.histPos[i];
                hist_nonbrown_acum[i] += calc.histNeg[i];
            }
            total_brown += calc.countPos;
            total_nonbrown += calc.countNeg;
            IJ.showStatus(
                    String.format("Ronda %d: %d pixeles positivos, %d negativos", ronda, calc.countPos, calc.countNeg));
            GenericDialog gd_mas = new GenericDialog("Agregar otra muestra?");
            gd_mas.addMessage(String.format(
                    "Ronda %d completada.\nPixeles positivos acumulados: %d\nPixeles negativos acumulados: %d\n\nPresione OK para agregar otra muestra en esta u otra imagen\no Cancel para finalizar el entrenamiento.",
                    ronda, total_brown, total_nonbrown));
            estilizarDialogo(gd_mas, false);
            gd_mas.showDialog();
            impFiltrada.changes = false;
            impFiltrada.close();
            if (gd_mas.wasCanceled())
                break;
            impActual.show();
            java.awt.Window win = impActual.getWindow();
            if (win != null) {
                WindowManager.setCurrentWindow((ij.gui.ImageWindow) win);
                win.toFront();
            }
            impActual.killRoi();
        }

        if (total_brown > 0 && total_nonbrown > 0) {
            for (int i = 0; i < 16384; i++) {
                prob_brown[i] = hist_brown_acum[i] / total_brown;
                prob_nonbrown[i] = hist_nonbrown_acum[i] / total_nonbrown;
            }
            modelo_cargado = true;
            IJ.showStatus("Entrenamiento completado - modelo listo");
        } else {
            IJ.showMessage("Error", "No se recopilaron suficientes datos para generar el modelo.");
            return;
        }

        GenericDialog gd_guardar = new GenericDialog("Guardar modelo?");
        gd_guardar.addMessage(
                "Desea guardar el modelo de entrenamiento?\nPresione OK para guardar o Cancel para omitir.");
        estilizarDialogo(gd_guardar, false);
        gd_guardar.showDialog();
        if (!gd_guardar.wasCanceled())
            guardarModeloDialogo();
    }

    private void guardarModeloDialogo() {
        SaveDialog sd = new SaveDialog("Guardar modelo de entrenamiento", "Entrenamiento_DAB", ".txt");
        String dir = sd.getDirectory();
        String name = sd.getFileName();
        if (dir == null || name == null)
            return;
        File file = new File(dir, name);
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(file))) {
            for (int i = 0; i < 128; i++) {
                for (int j = 0; j < 128; j++) {
                    int idx = i * 128 + j;
                    bw.write(String.format("%d\t%d\t%s\t%s\n", i, j, String.valueOf(prob_brown[idx]),
                            String.valueOf(prob_nonbrown[idx])));
                }
            }
            IJ.showMessage("Modelo guardado", "Modelo guardado exitosamente en:\n" + file.getAbsolutePath());
        } catch (Exception e) {
            IJ.showMessage("Error al guardar", e.getMessage());
        }
    }

    private void cargarModeloDialog() {
        OpenDialog od = new OpenDialog("Seleccionar archivo de entrenamiento (.txt)", "");
        String dir = od.getDirectory();
        String name = od.getFileName();
        if (dir == null || name == null)
            return;
        File file = new File(dir, name);
        try (BufferedReader br = new BufferedReader(new FileReader(file))) {
            String line;
            Arrays.fill(prob_brown, 0.0);
            Arrays.fill(prob_nonbrown, 0.0);
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty())
                    continue;
                String[] parts = line.split("\\s+");
                if (parts.length < 4)
                    continue;
                int cb_bin = Integer.parseInt(parts[0]);
                int cr_bin = Integer.parseInt(parts[1]);
                double p = Double.parseDouble(parts[2]);
                double np_val = Double.parseDouble(parts[3]);
                int idx = cb_bin * 128 + cr_bin;
                if (idx >= 0 && idx < 16384) {
                    prob_brown[idx] = p;
                    prob_nonbrown[idx] = np_val;
                }
            }
            modelo_cargado = true;
            // La ruta va a la barra de estado, que no estorba; el cartel queda limpio.
            IJ.showStatus("Modelo cargado desde: " + file.getAbsolutePath());
            IJ.showMessage("Modelo cargado", "MODELO CARGADO EXITOSAMENTE");
        } catch (Exception e) {
            IJ.showMessage("Error", "No se pudo cargar el modelo:\n" + e.getMessage());
        }
    }

    private class DABResult {
        ImagePlus impDab;
        long countPos;
    }

    private DABResult detectarDab(ImagePlus imp) {
        boolean[] isDabLut = new boolean[16384];
        for (int n = 0; n < 16384; n++) {
            double p = prob_brown[n];
            double pn = prob_nonbrown[n];
            if (p != 0.0 && pn == 0.0)
                isDabLut[n] = true;
            else if (pn != 0.0 && (p / pn) >= 0.7)
                isDabLut[n] = true;
        }

        int w = imp.getWidth(), h = imp.getHeight();
        ImagePlus impResult = IJ.createImage("Deteccion DAB", "RGB", w, h, 1);
        int[] pixelsOrig = (int[]) imp.getProcessor().getPixels();
        int[] pixelsRes = (int[]) impResult.getProcessor().getPixels();
        int blanco = 0x00FFFFFF, total = w * h;
        long countPositivo = 0;

        for (int k = 0; k < total; k++) {
            int c = pixelsOrig[k];
            int r = (c >> 16) & 0xFF, g = (c >> 8) & 0xFF, b = c & 0xFF;
            double cb = 0.5 * b - 0.169 * r - 0.331 * g + 128.0;
            double cr = 0.5 * r - 0.419 * g - 0.081 * b + 128.0;
            int i_cb = (int) Math.max(0, Math.min(127, cb / 2.0));
            int j_cr = (int) Math.max(0, Math.min(127, cr / 2.0));
            if (isDabLut[i_cb * 128 + j_cr]) {
                pixelsRes[k] = pixelsOrig[k];
                countPositivo++;
            } else {
                pixelsRes[k] = blanco;
            }
        }
        impResult.updateAndDraw();
        DABResult res = new DABResult();
        res.impDab = impResult;
        res.countPos = countPositivo;
        return res;
    }

    private void agregarEtiquetas(ResultsTable rt, String nombre, String imagen) {
        int idx = rt.size() - 1;
        rt.setValue("Nombre", idx, nombre);
        rt.setValue("Imagen", idx, imagen);
    }

    private void medirAreaTotal(ImagePlus imp, ResultsTable rt, String filename) {
        ImagePlus dup = imp.duplicate();
        IJ.run(dup, "8-bit", "");
        // Establecer umbral fijo: 0 a 230 (tejido). 231 a 255 es fondo blanco.
        dup.getProcessor().setThreshold(0, 230, ImageProcessor.NO_LUT_UPDATE);
        IJ.run(dup, "Convert to Mask", "");
        IJ.run(dup, "Measure", "");
        agregarEtiquetas(rt, "Area Total", filename);
        dup.changes = false;
        dup.close();
    }

    private void medirIntensidadDab(ImagePlus impDab, ResultsTable rt, String filename) {
        impDab.show();
        WindowManager.setCurrentWindow(impDab.getWindow());
        IJ.run("RGB Stack");
        IJ.run("Duplicate...", "duplicate range=2-2 use");
        ImagePlus impCanal = IJ.getImage();
        IJ.run(impCanal, "Invert", "");
        IJ.run(impCanal, "8-bit", "");
        // Umbral ABSOLUTO: Medir todo lo que no sea fondo (1 a 255)
        impCanal.getProcessor().setThreshold(1, 255, ImageProcessor.NO_LUT_UPDATE);
        IJ.run(impCanal, "Measure", "");
        agregarEtiquetas(rt, "Area e Intensidad de DAB", filename);
        impCanal.changes = false;
        impCanal.close();
    }

    private void renombrarArchivos(File rootDir) {
        if (!rootDir.isDirectory())
            return;
        File[] folders = rootDir.listFiles(File::isDirectory);
        if (folders != null) {
            for (File folder : folders) {
                String subfolder = folder.getName();
                File[] files = folder.listFiles((dir, name) -> {
                    String lw = name.toLowerCase();
                    return lw.endsWith(".tif") || lw.endsWith(".jpg") || lw.endsWith(".png");
                });
                if (files != null) {
                    for (File file : files) {
                        String fname = file.getName();
                        if (!fname.startsWith(subfolder + "_")) {
                            file.renameTo(new File(folder, subfolder + "_" + fname));
                        }
                    }
                }
            }
        }
    }

    private boolean procesarCarpeta(File rootDir) {
        IJ.run("Set Measurements...", "area mean standard stack limit display redirect=None decimal=2");
        ResultsTable rt = ResultsTable.getResultsTable();
        rt.reset(); // CORRECCIÓN: resetear la tabla para que no acumule datos de carpetas previas
        int count = 0;
        File[] folders = rootDir.listFiles(File::isDirectory);
        if (folders == null || folders.length == 0)
            folders = new File[] { rootDir };
        else {
            File[] all = new File[folders.length + 1];
            System.arraycopy(folders, 0, all, 0, folders.length);
            all[folders.length] = rootDir;
            folders = all;
        }

        FilenameFilter imgFilter = (dir, name) -> {
            String lw = name.toLowerCase();
            return lw.endsWith(".tif") || lw.endsWith(".jpg") || lw.endsWith(".png");
        };

        for (File folder : folders) {
            File[] files = folder.listFiles(imgFilter);
            if (files == null)
                continue;
            Arrays.sort(files);
            for (File file : files) {
                ImagePlus imp = IJ.openImage(file.getAbsolutePath());
                if (imp == null)
                    continue;
                IJ.showStatus("Procesando: " + file.getName());
                imp.show();
                DABResult dab = detectarDab(imp);
                dab.impDab.setTitle("Deteccion DAB - " + file.getName());
                medirAreaTotal(imp, rt, file.getName());
                medirIntensidadDab(dab.impDab, rt, file.getName());
                count++;
                dab.impDab.changes = false;
                dab.impDab.close();
                imp.changes = false;
                imp.close();
                IJ.run("Close All");
            }
        }

        if (rt != null && rt.size() > 0) {
            try {
                XSSFWorkbook wb = new XSSFWorkbook();
                XSSFSheet sheet = wb.createSheet("Resultados DAB");

                // Encabezados
                String[] columnas = {"Imagen", "Parametro", "Area", "Intensidad", "StdDev"};
                Row headerRow = sheet.createRow(0);
                for (int c = 0; c < columnas.length; c++) {
                    headerRow.createCell(c).setCellValue(columnas[c]);
                }

                // Datos
                for (int i = 0; i < rt.size(); i++) {
                    Row row = sheet.createRow(i + 1);
                    row.createCell(0).setCellValue(rt.getStringValue("Imagen", i));
                    row.createCell(1).setCellValue(rt.getStringValue("Nombre", i));
                    row.createCell(2).setCellValue(rt.getValue("Area", i));
                    row.createCell(3).setCellValue(rt.getValue("Mean", i));
                    row.createCell(4).setCellValue(rt.getValue("StdDev", i));
                }

                // Auto-ajustar ancho de columnas
                for (int c = 0; c < columnas.length; c++) {
                    sheet.autoSizeColumn(c);
                }

                String folderName = rootDir.getName();
                String outputName = "Resultados_DAB_" + folderName + ".xlsx";
                java.io.FileOutputStream fos = new java.io.FileOutputStream(new File(rootDir, outputName));
                wb.write(fos);
                fos.close();
                wb.close();
                IJ.showMessage("Proceso completado",
                        "Se analizaron " + count + " fotos.\nResultados guardados en: " + outputName);
            } catch (Exception e) {
                IJ.showMessage("Error", "No se pudo guardar el archivo de resultados.\n" + e.getMessage());
            }
        }

        // Cerrar la ventana "Results" correctamente.
        // IMPORTANTE: hay que usar TextWindow.close(), NO dispose(). ImageJ guarda una
        // referencia estatica al TextPanel de "Results" (IJ.textPanel) y solo
        // TextWindow.close() la pone en null (ademas de sacar la ventana del
        // WindowManager). Si se llama a dispose() directamente, esa referencia queda
        // apuntando a una ventana destruida: IJ.getTextPanel() la sigue devolviendo,
        // nunca se vuelve a crear la ventana "Results" y las mediciones posteriores
        // no se muestran hasta reiniciar Fiji.
        ij.plugin.filter.Analyzer.setUnsavedMeasurements(false); // evita el dialogo "Save N measurements?"
        if (rt != null)
            rt.reset();
        java.awt.Window[] wins = WindowManager.getNonImageWindows();
        if (wins != null) {
            for (java.awt.Window win : wins) {
                if (win instanceof ij.text.TextWindow && ((ij.text.TextWindow) win).getTitle().equals("Results")) {
                    ((ij.text.TextWindow) win).close(false);
                }
            }
        }
        return true;
    }
}
