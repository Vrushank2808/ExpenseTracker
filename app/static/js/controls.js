document.addEventListener("DOMContentLoaded", () => {
  window.setTimeout(() => document.body.classList.add("is-ready"), 350);

  document.querySelectorAll("a[href]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const target = link.getAttribute("target");
      const href = link.getAttribute("href");
      if (!event.defaultPrevented && target !== "_blank" && href && !href.startsWith("#") && !href.startsWith("mailto:")) {
        document.body.classList.add("is-loading");
      }
    });
  });

  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!event.defaultPrevented && form.checkValidity()) document.body.classList.add("is-loading");
    });
  });

  document.querySelectorAll(".flash").forEach((toast) => {
    window.setTimeout(() => toast.remove(), 4500);
  });

  const accountMenu = document.querySelector(".topbar-account");
  const accountTrigger = document.querySelector(".profile-menu-trigger");
  if (accountMenu && accountTrigger) {
    accountTrigger.addEventListener("click", () => {
      const opening = !accountMenu.classList.contains("open");
      accountMenu.classList.toggle("open", opening);
      accountTrigger.setAttribute("aria-expanded", opening ? "true" : "false");
    });
    accountTrigger.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        accountMenu.classList.remove("open");
        accountTrigger.setAttribute("aria-expanded", "false");
      }
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".topbar-account")) {
        accountMenu.classList.remove("open");
        accountTrigger.setAttribute("aria-expanded", "false");
      }
    });
  }

  const closeMenus = (except) => {
    document.querySelectorAll(".custom-select.open, .custom-date.open").forEach((control) => {
      if (control !== except) control.classList.remove("open");
    });
  };

  document.querySelectorAll("select").forEach((select) => {
    const wrapper = document.createElement("div");
    wrapper.className = "custom-select";
    select.parentNode.insertBefore(wrapper, select);
    wrapper.appendChild(select);
    select.classList.add("native-select");
    const wasRequired = select.required;
    select.required = false;

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "select-trigger";
    trigger.setAttribute("aria-haspopup", "listbox");
    trigger.setAttribute("aria-expanded", "false");
    const menu = document.createElement("div");
    menu.className = "select-menu";
    menu.setAttribute("role", "listbox");
    wrapper.append(trigger, menu);
    wrapper.dataset.required = wasRequired ? "true" : "false";

    const update = () => {
      const option = select.options[select.selectedIndex];
      trigger.textContent = option ? option.textContent : "Choose an option";
      trigger.classList.toggle("placeholder", !select.value);
      menu.querySelectorAll(".select-option").forEach((item) => {
        const selected = item.dataset.value === select.value;
        item.classList.toggle("selected", selected);
        item.setAttribute("aria-selected", selected ? "true" : "false");
      });
    };

    Array.from(select.options).forEach((option) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "select-option";
      item.textContent = option.textContent;
      item.dataset.value = option.value;
      item.setAttribute("role", "option");
      item.addEventListener("click", () => {
        select.value = option.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        update();
        wrapper.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
      });
      menu.appendChild(item);
    });

    trigger.addEventListener("click", () => {
      const opening = !wrapper.classList.contains("open");
      closeMenus(wrapper);
      wrapper.classList.toggle("open", opening);
      trigger.setAttribute("aria-expanded", opening ? "true" : "false");
    });
    trigger.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        wrapper.classList.add("open");
        trigger.setAttribute("aria-expanded", "true");
        menu.querySelector(".select-option")?.focus();
      }
      if (event.key === "Escape") wrapper.classList.remove("open");
    });
    select.addEventListener("change", update);
    update();

    if (wasRequired && select.form) {
      select.form.addEventListener("submit", (event) => {
        if (!select.value) {
          event.preventDefault();
          trigger.setAttribute("aria-invalid", "true");
          trigger.focus();
          wrapper.classList.add("open");
        } else {
          trigger.removeAttribute("aria-invalid");
        }
      });
    }
  });

  const pad = (number) => String(number).padStart(2, "0");
  const iso = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const displayDate = (date) => date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  const parseIso = (value) => {
    if (!value) return new Date();
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
  };

  document.querySelectorAll('input[type="date"]').forEach((nativeInput) => {
    const wrapper = document.createElement("div");
    wrapper.className = "custom-date";
    nativeInput.parentNode.insertBefore(wrapper, nativeInput);
    wrapper.appendChild(nativeInput);
    nativeInput.classList.add("native-date");
    const wasRequired = nativeInput.required;
    nativeInput.required = false;
    const selectedDate = parseIso(nativeInput.value);
    const display = document.createElement("input");
    display.type = "text";
    display.className = "date-display";
    display.readOnly = true;
    display.required = wasRequired;
    display.placeholder = "Choose a date";
    display.value = nativeInput.value ? displayDate(selectedDate) : "";
    display.setAttribute("aria-label", "Choose date");
    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "date-trigger";
    trigger.setAttribute("aria-label", "Open calendar");
    const picker = document.createElement("div");
    picker.className = "date-picker";
    picker.setAttribute("role", "dialog");
    picker.setAttribute("aria-label", "Calendar");
    wrapper.append(display, trigger, picker);
    let viewDate = new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1);

    const render = () => {
      picker.innerHTML = "";
      const header = document.createElement("div");
      header.className = "date-picker-header";
      const previous = document.createElement("button");
      previous.type = "button";
      previous.className = "date-nav";
      previous.textContent = "‹";
      previous.setAttribute("aria-label", "Previous month");
      const title = document.createElement("span");
      title.textContent = viewDate.toLocaleDateString("en-IN", { month: "long", year: "numeric" });
      const next = document.createElement("button");
      next.type = "button";
      next.className = "date-nav";
      next.textContent = "›";
      next.setAttribute("aria-label", "Next month");
      header.append(previous, title, next);
      picker.appendChild(header);
      previous.addEventListener("click", () => { viewDate.setMonth(viewDate.getMonth() - 1); render(); });
      next.addEventListener("click", () => { viewDate.setMonth(viewDate.getMonth() + 1); render(); });

      const week = document.createElement("div");
      week.className = "date-week";
      ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].forEach((day) => {
        const label = document.createElement("span");
        label.textContent = day;
        week.appendChild(label);
      });
      picker.appendChild(week);
      const grid = document.createElement("div");
      grid.className = "date-grid";
      const firstDay = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1).getDay();
      const daysInMonth = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0).getDate();
      for (let index = 0; index < firstDay; index += 1) grid.appendChild(document.createElement("span"));
      for (let day = 1; day <= daysInMonth; day += 1) {
        const current = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
        const button = document.createElement("button");
        button.type = "button";
        button.className = "date-day";
        button.textContent = day;
        button.dataset.date = iso(current);
        if (nativeInput.value === button.dataset.date) button.classList.add("selected");
        if (iso(new Date()) === button.dataset.date) button.classList.add("today");
        button.addEventListener("click", () => {
          nativeInput.value = button.dataset.date;
          display.value = displayDate(current);
          wrapper.classList.remove("open");
          render();
        });
        grid.appendChild(button);
      }
      picker.appendChild(grid);
    };

    const toggle = () => {
      const opening = !wrapper.classList.contains("open");
      closeMenus(wrapper);
      wrapper.classList.toggle("open", opening);
      if (opening) render();
    };
    display.addEventListener("click", toggle);
    trigger.addEventListener("click", toggle);
    if (nativeInput.form) {
      nativeInput.form.addEventListener("submit", (event) => {
        if (wasRequired && !nativeInput.value) {
          event.preventDefault();
          display.focus();
          wrapper.classList.add("open");
        }
      });
    }
    render();
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".custom-select, .custom-date")) closeMenus();
  });
});
