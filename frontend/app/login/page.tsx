import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';

async function login(formData: FormData) {
  'use server';
  if ((formData.get('password') as string) === process.env.AUTH_PASSWORD) {
    (await cookies()).set('auth', '1', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
    });
    redirect('/');
  }
}

export default function LoginPage() {
  return (
    <main className="flex h-screen items-center justify-center bg-gray-50">
      <form action={login} className="flex flex-col gap-4 bg-white p-8 rounded-xl shadow-sm border border-gray-200 w-72">
        <h1 className="text-lg font-semibold text-gray-800">VendorLens</h1>
        <input
          type="password"
          name="password"
          placeholder="Password"
          className="border border-gray-300 px-3 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gray-400"
          autoFocus
        />
        <button
          type="submit"
          className="bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700 transition-colors"
        >
          Enter
        </button>
      </form>
    </main>
  );
}
