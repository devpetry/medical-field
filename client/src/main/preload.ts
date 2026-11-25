import { contextBridge, ipcRenderer } from 'electron';

// Ponte mínima entre a interface (sem acesso ao Node) e o processo principal.
contextBridge.exposeInMainWorld('mf', {
  chamar: (metodo: string, ...args: unknown[]) => ipcRenderer.invoke('mf:chamar', metodo, args),
  salvarFicha: (atendimentoId: string) => ipcRenderer.invoke('mf:salvarFicha', atendimentoId),
  aoMudarEstado: (fn: (e: unknown) => void) => {
    const h = (_: unknown, e: unknown) => fn(e);
    ipcRenderer.on('mf:estado', h);
    return () => ipcRenderer.removeListener('mf:estado', h);
  },
});
