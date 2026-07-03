import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';

const url = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '';
const publishableKey = process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? '';
export const isSupabaseConfigured = Boolean(url && publishableKey);

const serverStorage = {
  getItem: async (_key: string) => null,
  setItem: async (_key: string, _value: string) => undefined,
  removeItem: async (_key: string) => undefined,
};
const authStorage = typeof window === 'undefined' ? serverStorage : AsyncStorage;

export const supabase = isSupabaseConfigured ? createClient(url, publishableKey, {
  auth: {
    storage: authStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
}) : null;

export async function authToken(): Promise<string> {
  if (__DEV__ && !supabase) return 'dev-token';
  if (!supabase) throw new Error('Sign in is not configured');
  const { data, error } = await supabase.auth.getSession();
  if (error || !data.session) throw new Error('Sign in to contribute a road report');
  return data.session.access_token;
}

export async function hasSession(): Promise<boolean> {
  if (__DEV__ && !supabase) return true;
  if (!supabase) return false;
  const { data } = await supabase.auth.getSession();
  return Boolean(data.session);
}

export async function signIn(email: string, password: string) {
  if (!supabase) throw new Error('Supabase environment variables are not configured');
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function signUp(email: string, password: string) {
  if (!supabase) throw new Error('Supabase environment variables are not configured');
  const { error } = await supabase.auth.signUp({ email, password });
  if (error) throw error;
}
