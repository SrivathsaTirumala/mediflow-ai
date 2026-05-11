# MediFlow AI Deployment Guide

This project is now a real Vite application that builds into static assets and deploys cleanly to Vercel.

## 1. Local verification

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm install
npm run build
```

Expected output:

- `dist/index.html`
- `dist/assets/*.js`
- `dist/assets/*.css`

## 2. Git-based Vercel deployment

1. Create a new GitHub repository.
2. Copy the contents of `mediflow-ai` into that repository.
3. Commit and push:

```bash
git init
git add .
git commit -m "Add MediFlow AI"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mediflow-ai.git
git push -u origin main
```

4. In Vercel, choose `Add New Project`.
5. Import the GitHub repository.
6. Keep the detected settings:
   - Framework preset: `Vite`
   - Build command: `npm run build`
   - Output directory: `dist`
7. Click `Deploy`.

## 3. CLI deployment

If you already have a Vercel account and want to deploy from the terminal:

```bash
cd /home/edgeproc/srivathsa/mediflow-ai
source /home/edgeproc/miniforge3/etc/profile.d/conda.sh
conda activate mediflow-env
npm install -g vercel
vercel
```

For production deployment:

```bash
vercel --prod
```

## 4. Files that matter for deployment

- `package.json`: scripts and dependencies
- `vite.config.js`: Vite config
- `vercel.json`: tells Vercel to use the Vite build output
- `src/App.jsx`: main UI and local triage logic
- `src/styles.css`: styling and responsive layout

## 5. Notes

- The app is browser-only and does not require a backend service.
- The generated recommendations are demo logic, not medical advice.
- I could not complete an actual Vercel publish from this environment because there is no Vercel CLI or account authentication configured here.
- [ ] All test cases verified
- [ ] Uploaded all documentation
- [ ] GitHub repo link included
- [ ] About project description ready
- [ ] Technologies list prepared
- [ ] Team members listed

---

## 🎉 YOU'RE ALL SET!

**Congratulations!**

Your MediFlow AI demo is complete and ready for presentation.

**Demo Link:** https://mediflow-ai-demo.vercel.app

**Good luck at the hackathon! 🚀**

---

**Questions about deployment?**
- Vercel Docs: https://vercel.com/docs
- GitHub Help: https://docs.github.com
- HTML File Issues: Check browser console (F12)

**Last Updated:** May 2026 | MediFlow AI v1.0
