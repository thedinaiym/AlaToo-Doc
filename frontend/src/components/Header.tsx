import Image from "next/image";

export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
      <div className="text-xl font-bold text-blue-700">Alatoo-Doc</div>

      <Image
        src="/logo.png"
        width={130}
        height={45}
        alt="University logo"
        priority
      />
    </header>
  );
}
