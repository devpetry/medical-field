import { app, BrowserWindow, dialog, ipcMain } from 'electron';
import { writeFile } from 'node:fs/promises';
import path from 'node:path';
import { MedicalFieldCore } from './core';

// API_URL: endereço do Nginx na VM (ex.: http://10.0.0.10/api).
const API_URL = process.env.API_URL ?? 'http://127.0.0.1/api';
let core: MedicalFieldCore;
let janela: BrowserWindow | null = null;

// Métodos do núcleo que a interface pode chamar via IPC.
const METODOS = [
  'estado', 'login', 'logout', 'definirSimulacao', 'sincronizar', 'listarPessoas', 'salvarPessoa', 'prontuarioDaPessoa',
  'salvarProntuario', 'listarMedicamentos', 'listarAtendimentos', 'validarAtendimento', 'salvarAtendimento',
  'listarOutbox', 'listarLogs', 'enviarFicha',
] as const;

function criarJanela() {
  janela = new BrowserWindow({
    width: 1440, height: 920, minWidth: 1100, minHeight: 720, backgroundColor: '#071224',
    title: 'MedicalField · Cliente',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false, sandbox: true },
  });
  janela.setMenuBarVisibility(false);
  void janela.loadFile(path.join(__dirname, '..', '..', 'dist-renderer', 'index.html'));

  // Captura de tela para testes automatizados: MF_SCREENSHOT=arquivo.png
  const alvo = process.env.MF_SCREENSHOT;
  if (alvo) {
    janela.webContents.once('did-finish-load', () => setTimeout(async () => {
      const img = await janela!.webContents.capturePage();
      await writeFile(alvo, img.toPNG());
      app.quit();
    }, Number(process.env.MF_SCREENSHOT_DELAY ?? 2500)));
  }
}

app.whenReady().then(() => {
  core = new MedicalFieldCore({
    arquivoBanco: process.env.MF_DB ?? path.join(app.getPath('userData'), 'medicalfield.db'),
    apiUrl: API_URL,
    deviceId: process.env.DEVICE_ID,
  });
  core.aoMudarEstado((e) => janela?.webContents.send('mf:estado', e));

  ipcMain.handle('mf:chamar', async (_ev, metodo: string, args: unknown[]) => {
    if (!(METODOS as readonly string[]).includes(metodo)) throw new Error(`Método não permitido: ${metodo}`);
    const fn = (core as unknown as Record<string, (...a: unknown[]) => unknown>)[metodo];
    return fn.apply(core, args);
  });

  ipcMain.handle('mf:salvarFicha', async (_ev, atendimentoId: string) => {
    const pdf = await core.fichaPdf(atendimentoId);
    const r = await dialog.showSaveDialog(janela!, {
      title: 'Salvar Ficha de Atendimento',
      defaultPath: path.join(app.getPath('downloads'), `ficha_atendimento_${atendimentoId.slice(0, 8)}.pdf`),
      filters: [{ name: 'PDF', extensions: ['pdf'] }],
    });
    if (r.canceled || !r.filePath) return null;
    await writeFile(r.filePath, pdf);
    return r.filePath;
  });

  criarJanela();
  core.iniciar();
});

app.on('window-all-closed', () => {
  core?.encerrar();
  app.quit();
});
