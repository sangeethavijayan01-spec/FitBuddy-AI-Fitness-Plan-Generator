document.querySelectorAll("form").forEach(f=>f.addEventListener("submit",()=>{const b=f.querySelector("button[type=submit],button:not([type])");if(b){b.disabled=true;b.dataset.old=b.textContent;b.textContent="Working…";}}));
const search=document.querySelector("#foodSearch"); const cards=[...document.querySelectorAll(".food-card")]; const filters=[...document.querySelectorAll(".filter")]; let active="all";
function filterFoods(){const q=(search?.value||"").toLowerCase().trim(); cards.forEach(c=>{const okCategory=active==="all"||c.dataset.category===active; const okQuery=!q||c.dataset.name.includes(q); c.style.display=okCategory&&okQuery?"block":"none";});}
search?.addEventListener("input",filterFoods); filters.forEach(btn=>btn.addEventListener("click",()=>{filters.forEach(x=>x.classList.remove("active"));btn.classList.add("active");active=btn.dataset.filter;filterFoods();}));
const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add("in-view");observer.unobserve(e.target);}}),{threshold:.08}); document.querySelectorAll(".reveal").forEach(el=>observer.observe(el));


// Weekly day checklist: save each click immediately and update the percentage without reloading.
document.querySelectorAll('.day-check input').forEach(box => {
  box.addEventListener('change', async () => {
    const wrap = box.closest('.day-check');
    wrap.classList.toggle('checked', box.checked);
    box.disabled = true;
    try {
      const body = new URLSearchParams({completed: String(box.checked)});
      const res = await fetch(`/plan/${wrap.dataset.planId}/day/${wrap.dataset.day}/toggle`, {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body});
      if (!res.ok) throw new Error('save failed');
      const data = await res.json();
      document.querySelector('#completionPercent').textContent = `${data.percent}%`;
      document.querySelector('#completedCount').textContent = data.completed_count;
    } catch (e) {
      box.checked = !box.checked;
      wrap.classList.toggle('checked', box.checked);
      alert('Could not save this day. Please try again.');
    } finally { box.disabled = false; }
  });
});
