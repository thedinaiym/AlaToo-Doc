import Image from "next/image";

export default function Header() {
  return (
    <header className="flex items-center justify-between bg-white px-6 py-4 shadow-sm">
      <div className="text-xl font-bold text-blue-700">Alatoo-Doc</div>

      <Image
        src="/logo.png"
        width={120}
        height={40}
        alt="University logo"
        priority
      />
    </header>
  );
}
