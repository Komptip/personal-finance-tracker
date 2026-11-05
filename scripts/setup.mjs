import { spawnSync } from 'node:child_process'
import { existsSync, readFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

const root = fileURLToPath(new URL('../', import.meta.url))
process.chdir(root)
if (Number(process.versions.node.split('.')[0]) < 22) {
  console.error('Node 22 or newer is required. In WSL: nvm install && nvm use')
  process.exit(1)
}
function run(command, args) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    env: { ...process.env, NUXT_TELEMETRY_DISABLED: '1' },
  })
  if (result.error || result.status !== 0) {
    console.error(`Setup stopped: ${command} failed. See docs/SETUP.md.`)
    process.exit(result.status || 1)
  }
}
const python = ['python3', 'python'].find((command) => {
  const result = spawnSync(command, ['-c', 'import sys; sys.exit(sys.version_info < (3, 10))'])
  return !result.error && result.status === 0
})
if (!python) {
  console.error('Python 3.10+ is required. See docs/SETUP.md for WSL installation.')
  process.exit(1)
}
const npmCli = process.env.npm_execpath
if (!npmCli) throw new Error('Run this script with npm run setup')
run(process.execPath, [npmCli, 'ci', '--no-audit', '--no-fund'])
for (const directory of ['private/imports', 'data/processed'])
  mkdirSync(directory, { recursive: true })
let dataFile = process.env.NUXT_DATA_FILE || 'data/processed/tagged_transactions.csv'
if (!process.env.NUXT_DATA_FILE && existsSync('.env')) {
  const match = readFileSync('.env', 'utf8').match(/^NUXT_DATA_FILE\s*=\s*(.+)$/m)
  if (match) dataFile = match[1].trim().replace(/^(['"])(.*)\1$/, '$2')
}
if (existsSync(resolve(root, dataFile))) {
  console.log('Existing local dataset kept unchanged.')
} else if (dataFile === 'data/processed/tagged_transactions.csv') {
  run(python, ['-m', 'pipeline', 'demo', '--if-missing'])
} else {
  console.log(
    'Custom NUXT_DATA_FILE is missing. Import data there or update .env; no demo was written.',
  )
}
// Install a repository-local hook only if it will not replace an existing hook configuration.
const hookPath = spawnSync('git', ['config', '--get', 'core.hooksPath'], { encoding: 'utf8' })
if (existsSync('.git') && !hookPath.stdout?.trim()) {
  run('git', ['config', '--local', 'core.hooksPath', '.githooks'])
}
console.log('Setup complete. Run npm run dev, then open http://localhost:3000.')
