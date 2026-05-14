import { createConfig, http } from "wagmi";
import { baseSepolia } from "wagmi/chains";
import { injected, metaMask } from "wagmi/connectors";

export const wagmiConfig = createConfig({
  chains: [baseSepolia],
  connectors: [metaMask(), injected()],
  transports: {
    [baseSepolia.id]: http(),
  },
  ssr: true,
});
