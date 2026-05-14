import type { Account, WalletClient } from "viem";
import { toClientEvmSigner } from "@x402/evm";
import type { ClientEvmSigner } from "@x402/evm";

type ReadContractCapablePublicClient = {
  readContract: (args: {
    address: `0x${string}`;
    abi: readonly unknown[];
    functionName: string;
    args?: readonly unknown[];
  }) => Promise<unknown>;
};

export function walletClientToX402Signer(
  walletClient: WalletClient,
  publicClient: ReadContractCapablePublicClient,
): ClientEvmSigner {
  if (!walletClient.account) {
    throw new Error("Wallet client must have an account");
  }
  const account = walletClient.account as Account;

  return toClientEvmSigner(
    {
      address: account.address,
      signTypedData: (message) =>
        walletClient.signTypedData({
          account,
          domain: message.domain,
          types: message.types,
          primaryType: message.primaryType,
          message: message.message,
        }),
    },
    {
      readContract: (args) =>
        publicClient.readContract({
          address: args.address,
          abi: args.abi,
          functionName: args.functionName,
          args: args.args,
        }),
    },
  );
}
