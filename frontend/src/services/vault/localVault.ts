/**
 * DecentralID Encrypted Client-Side Local Credential Vault
 * Utilizes Web Crypto API (PBKDF2 + AES-256-GCM) to encrypt credentials locally in IndexedDB.
 * Zero plaintext credential storage in ordinary localStorage.
 */

export interface EncryptedVaultPayload {
  version: number;
  salt: string; // Base64
  iv: string;   // Base64
  ciphertext: string; // Base64
  tagLength: number;
}

export class LocalVaultService {
  public static readonly DB_NAME = 'DecentralID_Vault';
  public static readonly STORE_NAME = 'credentials';
  private static PBKDF2_ITERATIONS = 100000;

  private static async deriveKey(passphrase: string, salt: Uint8Array): Promise<CryptoKey> {
    const enc = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      enc.encode(passphrase),
      { name: 'PBKDF2' },
      false,
      ['deriveKey']
    );

    return window.crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: salt as BufferSource,
        iterations: this.PBKDF2_ITERATIONS,
        hash: 'SHA-256',
      },
      keyMaterial,
      { name: 'AES-GCM', length: 256 },
      false,
      ['encrypt', 'decrypt']
    );
  }

  /**
   * Encrypts plaintext credentials using AES-256-GCM derived from holder passphrase/PIN.
   */
  public static async encryptVaultData(
    data: unknown,
    passphrase: string
  ): Promise<EncryptedVaultPayload> {
    const salt = window.crypto.getRandomValues(new Uint8Array(16));
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const key = await this.deriveKey(passphrase, salt);

    const encoded = new TextEncoder().encode(JSON.stringify(data));
    const encrypted = await window.crypto.subtle.encrypt(
      { name: 'AES-GCM', iv: iv as BufferSource, tagLength: 128 },
      key,
      encoded
    );

    return {
      version: 1,
      salt: btoa(String.fromCharCode(...salt)),
      iv: btoa(String.fromCharCode(...iv)),
      ciphertext: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
      tagLength: 128,
    };
  }

  /**
   * Decrypts ciphertext credentials. Rejects invalid passphrase with an explicit error.
   */
  public static async decryptVaultData(
    payload: EncryptedVaultPayload,
    passphrase: string
  ): Promise<unknown> {
    const salt = new Uint8Array(
      atob(payload.salt)
        .split('')
        .map((c) => c.charCodeAt(0))
    );
    const iv = new Uint8Array(
      atob(payload.iv)
        .split('')
        .map((c) => c.charCodeAt(0))
    );
    const ciphertext = new Uint8Array(
      atob(payload.ciphertext)
        .split('')
        .map((c) => c.charCodeAt(0))
    );

    const key = await this.deriveKey(passphrase, salt);

    try {
      const decrypted = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv as BufferSource, tagLength: payload.tagLength },
        key,
        ciphertext
      );
      const decoded = new TextDecoder().decode(decrypted);
      return JSON.parse(decoded);
    } catch {
      throw new Error('VAULT_DECRYPTION_FAILED: Invalid passphrase or corrupted vault payload.');
    }
  }

  /**
   * Exports encrypted backup string for portable holder backup.
   */
  public static async exportEncryptedBackup(credentials: unknown, passphrase: string): Promise<string> {
    const payload = await this.encryptVaultData(credentials, passphrase);
    return JSON.stringify(payload, null, 2);
  }

  /**
   * Restores credentials from an encrypted backup string.
   */
  public static async importEncryptedBackup(backupJson: string, passphrase: string): Promise<unknown> {
    try {
      const payload: EncryptedVaultPayload = JSON.parse(backupJson);
      if (!payload.ciphertext || !payload.iv || !payload.salt) {
        throw new Error('INVALID_BACKUP_FORMAT');
      }
      return await this.decryptVaultData(payload, passphrase);
    } catch (e: unknown) {
      if (e instanceof Error && e.message.startsWith('VAULT_DECRYPTION_FAILED')) {
        throw e;
      }
      throw new Error('INVALID_BACKUP_FORMAT: Corrupted or unparseable backup file.');
    }
  }
}
