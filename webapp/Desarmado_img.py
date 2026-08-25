import cv2
import os
import json
import numpy as np

def interpolate_frame(frame1, frame2, alpha):
    """
    Interpola entre dos frames usando blend lineal.
    
    Args:
        frame1: Primer frame
        frame2: Segundo frame
        alpha: Factor de interpolación (0.0 a 1.0)
    
    Returns:
        Frame interpolado
    """
    return cv2.addWeighted(frame1, 1 - alpha, frame2, alpha, 0)

def extract_and_interpolate_frames(video_path, output_dir, target_frames=100):
    """
    Extrae frames del video e interpola entre ellos para generar más frames suavemente.
    
    Args:
        video_path: Ruta del video
        output_dir: Directorio donde guardar las imágenes
        target_frames: Número de frames objetivo (60-120)
    """
    
    # Crear directorio de salida si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Limpiar frames anteriores
    for f in os.listdir(output_dir):
        if f.startswith('frame_') and f.endswith('.jpg'):
            os.remove(os.path.join(output_dir, f))
    
    # Abrir el video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: No se pudo abrir el video {video_path}")
        return False
    
    # Obtener información del video
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"Video info:")
    print(f"  - Total frames: {total_frames}")
    print(f"  - FPS: {fps}")
    print(f"  - Resolución: {width}x{height}")
    print(f"  - Duración: {duration:.2f}s")
    print(f"\nGenerando {target_frames} frames con interpolación...\n")
    
    # Leer todos los frames del video
    original_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        original_frames.append(frame)
    
    cap.release()
    
    # Calcular cuántos frames interpolados por cada par de frames originales
    num_original = len(original_frames)
    
    # Mejor distribución: para cada segmento de 2 frames originales, generar múltiples interpolados
    # Si tenemos 46 frames y queremos 80, necesitamos aproximadamente 1-2 frames interpolados por segmento
    num_segments = num_original - 1  # 45 segmentos
    frames_per_segment = target_frames / num_segments  # ~1.78 frames por segmento
    
    # Almacenar frames interpolados y metadata
    all_frames = []
    frame_data = []
    output_index = 0
    
    # Procesar cada par de frames consecutivos
    for i in range(num_original - 1):
        frame1 = original_frames[i]
        frame2 = original_frames[i + 1]
        
        # Calcular cuántos frames interpolar en este segmento
        # Usar un algoritmo más preciso para distribuir uniformemente
        frames_so_far = i * frames_per_segment
        frames_target = (i + 1) * frames_per_segment
        num_interp = max(1, int(round(frames_target - frames_so_far)))
        
        # Asegurar que no excedamos target_frames
        if output_index + num_interp > target_frames:
            num_interp = target_frames - output_index
        
        # Generar frames interpolados
        for j in range(num_interp):
            if j == 0 and i == 0:
                # Primer frame absoluto
                interp_frame = frame1
            elif j == 0:
                # Otros primeros frames del segmento son interpolados (no los originales)
                alpha = 0.0
                interp_frame = frame1
            else:
                # Interpolar entre frame1 y frame2
                alpha = j / num_interp
                interp_frame = interpolate_frame(frame1, frame2, alpha)
            
            # Guardar frame
            filename = f"frame_{output_index:03d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, interp_frame)
            
            # Timestamp basado en posición en la secuencia
            timestamp = (output_index / target_frames) * duration
            
            frame_data.append({
                "index": output_index,
                "segment": i,
                "interpolation": j,
                "timestamp": round(timestamp, 3),
                "filename": filename
            })
            
            all_frames.append(interp_frame)
            output_index += 1
            
            if output_index % 10 == 0:
                print(f"  Procesados {output_index}/{target_frames} frames...")
    
    # Agregar último frame original
    last_frame = original_frames[-1]
    filename = f"frame_{output_index:03d}.jpg"
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, last_frame)
    
    timestamp = duration
    frame_data.append({
        "index": output_index,
        "segment": num_original - 1,
        "interpolation": 0,
        "timestamp": round(timestamp, 3),
        "filename": filename
    })
    
    output_index += 1
    
    # Guardar metadata en JSON
    metadata = {
        "video_info": {
            "original_frames": num_original,
            "total_frames": total_frames,
            "fps": fps,
            "width": width,
            "height": height,
            "duration": duration
        },
        "extraction_info": {
            "frames_generated": output_index,
            "target_frames": target_frames,
            "method": "interpolation",
            "frames_per_segment": round(frames_per_segment, 2)
        },
        "frames": frame_data
    }
    
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Proceso completado!")
    print(f"  - {output_index} frames generados en: {output_dir}")
    print(f"  - Método: Interpolación suave entre frames")
    print(f"  - Metadata guardada en: {metadata_path}")
    
    return True

# Script principal
if __name__ == "__main__":
    # Rutas
    video_path = "./media/video/Helado_Video_2k.mp4"
    output_dir = "./media/frames"
    target_frames = 100  # Volver a 100 frames
    
    # Convertir a ruta absoluta si es necesario
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path_abs = os.path.join(script_dir, video_path)
    output_dir_abs = os.path.join(script_dir, output_dir)
    
    print(f"Buscando video en: {video_path_abs}\n")
    
    # Verificar que el video existe
    if not os.path.exists(video_path_abs):
        print(f"Error: El archivo {video_path_abs} no existe")
        print(f"Intenta verificar la ruta del video")
    else:
        # Extraer e interpolar frames
        extract_and_interpolate_frames(video_path_abs, output_dir_abs, target_frames=target_frames)


