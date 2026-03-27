import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig(({ command }) => ({
	plugins: [svelte()],
	publicDir: 'static',
	base: command === 'serve' ? '/' : '/districts/',
	build: {
		outDir: 'dist',
		assetsDir: 'assets'
	},
	server: {
		port: 5173
	}
}));

