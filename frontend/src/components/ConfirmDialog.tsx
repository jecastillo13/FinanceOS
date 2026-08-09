import { AlertTriangle, X } from "lucide-react";

export default function ConfirmDialog({title,description,confirmLabel="Eliminar",busy=false,onCancel,onConfirm}:{title:string;description:string;confirmLabel?:string;busy?:boolean;onCancel:()=>void;onConfirm:()=>void}){
 return <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="confirm-title"><button className="modal-backdrop" aria-label="Cerrar" onClick={onCancel}/><div className="confirm-dialog"><button className="confirm-close" onClick={onCancel}><X/></button><span className="confirm-icon"><AlertTriangle/></span><span className="eyebrow">CONFIRMACIÓN SEGURA</span><h3 id="confirm-title">{title}</h3><p>{description}</p><div><button className="ghost-action" onClick={onCancel}>Cancelar</button><button className="danger-action" onClick={onConfirm} disabled={busy}>{busy?"Procesando…":confirmLabel}</button></div></div></div>;
}
