import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Footer } from './Footer';
import { useWallet } from '../../features/authentication/hooks/useWallet';

export const AppLayout: React.FC = () => {
  const { account, chainId, isConnecting, connectWallet, disconnectWallet } = useWallet();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isOpenMobile, setIsOpenMobile] = useState(false);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex flex-1">
        {/* Navigation Sidebar */}
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          isOpenMobile={isOpenMobile}
          onCloseMobile={() => setIsOpenMobile(false)}
          chainId={chainId}
        />

        {/* Main Content Shell */}
        <div className="flex-1 flex flex-col min-w-0">
          <Header
            account={account}
            chainId={chainId}
            isConnecting={isConnecting}
            onConnect={connectWallet}
            onDisconnect={disconnectWallet}
            onToggleMobileMenu={() => setIsOpenMobile(true)}
          />

          <main className="flex-1 px-4 sm:px-6 lg:px-8 py-8 max-w-7xl w-full mx-auto">
            <Outlet />
          </main>

          <Footer />
        </div>
      </div>
    </div>
  );
};
