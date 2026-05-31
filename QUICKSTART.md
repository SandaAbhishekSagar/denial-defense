# 🚀 QUICK START CARD

**Status:** ✅ Build Complete | ⏰ 6+ hours to deadline

## Next 3 Steps (5 minutes)

```bash
# 1. Create .env
cp .env.example .env

# 2. Edit .env - add your keys:
#    OPENAI_API_KEY=sk-...
#    WANDB_API_KEY=...

# 3. Test baseline
python agents/baseline.py
```

If baseline works ✅ → Run harness:
```bash
python agents/harness.py
```

If harness works ✅ → Launch web UI:
```bash
python web/app.py
# Open http://localhost:5000
```

---

## 📚 Documentation Map

- **LAUNCH.md** ← Start here (you are here!)
- **STATUS.md** - Full build report + troubleshooting
- **HARNESS_README.md** - Technical documentation
- **BUILD_SUMMARY.md** - Implementation details

---

## 🎯 What's Built

✅ Multi-agent harness (LangGraph)  
✅ 6 agent prompts (3 patient + critic + supervisor + baseline)  
✅ Flask web UI (3 demo cases)  
✅ Weave evaluation  
✅ Complete docs

---

## ⚡ If Stuck

1. Run verification: `python scripts/verify_setup.py`
2. Check STATUS.md troubleshooting section
3. All code includes error handling - read error messages

---

## 🎤 30-Second Pitch

"Three patient agents work in parallel pulling clinical evidence, policy criteria, and precedent. An adversarial critic — simulating the insurer's medical reviewer — attacks the weakest claim. Patient agents revise. Two rounds of critique. The appeal you get is a third draft that survived two attacks, backed by real California IMR precedent from 42,000 cases."

---

**GO!** Add API keys and test! 🚀
