.PHONY: start backend frontend

start:
	./start_jarvis.sh

backend:
	cd jarvis-system/backend && python3 main.py

frontend:
	cd jarvis-system/frontend && npm run dev