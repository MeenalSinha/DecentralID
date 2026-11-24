import { useState, useEffect, useCallback } from 'react';
import { BrowserProvider, JsonRpcSigner } from 'ethers';

declare global {
  interface Window {
    ethereum?: any;
  }
}

export function useWallet() {
  const [account, setAccount] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [signer, setSigner] = useState<JsonRpcSigner | null>(null);
  const [provider, setProvider] = useState<BrowserProvider | null>(null);
  const [isConnecting, setIsConnecting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const updateWalletState = useCallback(async (browserProvider: BrowserProvider) => {
    try {
      const network = await browserProvider.getNetwork();
      setChainId(Number(network.chainId));
      const rpcSigner = await browserProvider.getSigner();
      const address = await rpcSigner.getAddress();
      setSigner(rpcSigner);
      setAccount(address);
      setError(null);
    } catch (err: any) {
      console.error('Failed to get signer:', err);
      setAccount(null);
      setSigner(null);
    }
  }, []);

  const connectWallet = useCallback(async () => {
    if (!window.ethereum) {
      setError('Please install an Ethereum wallet like MetaMask to connect.');
      return;
    }

    setIsConnecting(true);
    setError(null);
    try {
      const browserProvider = new BrowserProvider(window.ethereum);
      setProvider(browserProvider);
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      await updateWalletState(browserProvider);
    } catch (err: any) {
      setError(err.message || 'Failed to connect wallet');
    } finally {
      setIsConnecting(false);
    }
  }, [updateWalletState]);

  const disconnectWallet = useCallback(() => {
    setAccount(null);
    setSigner(null);
    setProvider(null);
  }, []);

  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          disconnectWallet();
        } else if (provider) {
          updateWalletState(provider);
        }
      };

      const handleChainChanged = () => {
        window.location.reload();
      };

      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', handleChainChanged);

      return () => {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
        window.ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, [provider, disconnectWallet, updateWalletState]);

  return {
    account,
    chainId,
    signer,
    provider,
    isConnecting,
    error,
    connectWallet,
    disconnectWallet,
  };
}
