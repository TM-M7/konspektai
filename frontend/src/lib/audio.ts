export interface AudioMetrics {
  durationSeconds: number;
  averageVolume: number;
  peakVolume: number;
}

export async function blobToBase64(blob: Blob): Promise<string> {
  const buffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";

  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }

  return window.btoa(binary);
}

export async function analyzeAudioBlob(blob: Blob): Promise<AudioMetrics> {
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new AudioContext();

  try {
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0));
    const channelData = audioBuffer.getChannelData(0);

    if (channelData.length === 0) {
      return { durationSeconds: 0, averageVolume: 0, peakVolume: 0 };
    }

    let absoluteSum = 0;
    let peakVolume = 0;

    for (const sample of channelData) {
      const amplitude = Math.abs(sample);
      absoluteSum += amplitude;
      if (amplitude > peakVolume) {
        peakVolume = amplitude;
      }
    }

    return {
      durationSeconds: Number(audioBuffer.duration.toFixed(2)),
      averageVolume: Number((absoluteSum / channelData.length).toFixed(2)),
      peakVolume: Number(peakVolume.toFixed(2)),
    };
  } finally {
    await audioContext.close();
  }
}

export function detectAudioFormat(mimeType: string): string {
  const [, subtype = "webm"] = mimeType.split("/");
  return subtype.split(";")[0] || "webm";
}
