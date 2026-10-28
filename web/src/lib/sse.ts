// Typed Server-Sent Events helper. Each message is JSON parsed into T.
// Returns an unsubscribe function that closes the stream.
export function subscribe<T>(
  url: string,
  onEvent: (event: T) => void,
  onError?: (error: Event) => void,
): () => void {
  const source = new EventSource(url);
  source.onmessage = (message) => onEvent(JSON.parse(message.data) as T);
  source.onerror = (error) => onError?.(error);
  return () => source.close();
}
