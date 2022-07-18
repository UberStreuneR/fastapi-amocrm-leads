var data = {
  // companyFields: [
  //   { value: "1234232", label: "Email" },
  //   { value: "3334322", label: "Web" },
  //   { value: "3234562", label: "Адрес" },
  //   { value: "4234", label: "Примечание" },
  //   { value: "23412", label: "Почтовый адрес" },
  //   { value: "34533", label: "Последняя оплата" },
  //   { value: "23452345", label: "Уровень компании" },
  //   { value: "3433347", label: "Сумма оплат за 6 мес." },
  // ],
  // leadFields: [
  //   { value: "1", label: "Сообщ. в Телеграм" },
  //   { value: "2", label: "Кол-во успешных сделок за 6 мес." },
  //   { value: "3", label: "на дату" },
  //   { value: "4", label: "Этап 'Завершены работы'" },
  //   { value: "5", label: "Сделка для возврата залога?" },
  //   { value: "6", label: "Воронка Первичное этап Закрыто" },
  // ],
  // contactFields: [
  //   { value: "1", label: "Примечание" },
  //   { value: "2", label: "Регион" },
  //   { value: "3", label: "Уровень контакта" },
  //   { value: "4", label: "Кол-во успешных сделок за 6 мес." },
  //   { value: "5", label: "roistat" },
  // ],
  dependencyTypes: [
    { value: "quantity", label: "От количества" },
    { value: "sum", label: "От суммы" },
  ],
  entityTypes: [
    { value: "contact", label: "Контакт" },
    { value: "company", label: "Компания" },
  ],
};

define(["./templates.js"], function (templatesRenderer) {
  class Widget {
    constructor(widget, getTemplate) {
      this.widget = widget;
      this.getTemplate = getTemplate;
      this.isDestroyed = false;

      this.companyFields = [];
      this.contactFields = [];
      this.leadFields = [];
      this.dependencyTypes = data["dependencyTypes"];
      this.entityTypes = data["entityTypes"];
    }

    makeRequest({ method, path, data, successful, complete } = {}) {
      this.widget.$authorizedAjax({
        url: `${this.widget.get_settings().serverURL}/${path}`,
        type: method,
        data: JSON.stringify(data),
        dataType: "json",
        contentType: "application/json",
        complete,
        success: data => {
          if (!this.isDestoryed) {
            successful(data);
          }
        },
        error: () => {
          AMOCRM.notifications.show_message({
            header: this.widget.langs.widget.name,
            text: this.widget.langs.ui.badRequest,
          });
        },
      });
    }

    optionsToItems({ options, values, prefix } = {}) {
      return options.reduce((items, option) => {
        let item = { id: option.value, option: option.label };
        if (values && prefix) {
          item.name = `${prefix}${option.value}`;
          item.is_checked = values.includes(option.value);
          item.option = `${option.group}. ${item.option}`;
        }

        items.push(item);
        return items;
      }, []);
    }

    returnItems() {
      const companyItems = this.optionsToItems({
        options: this.companyFields,
      });
      const leadItems = this.optionsToItems({ options: this.leadFields });
      const contactItems = this.optionsToItems({
        options: this.contactFields,
      });
      const dependencyItems = this.optionsToItems({
        options: this.dependencyTypes,
      });
      const entityItems = this.optionsToItems({ options: this.entityTypes });
      return {
        companyItems,
        leadItems,
        contactItems,
        dependencyItems,
        entityItems,
      };
    }

    checkItems() {
      return this.companyFields;
    }

    addDeleteButtonListeners() {
      var tbody = document.querySelector("#status-tab tbody");
      tbody.addEventListener("click", e => {
        if (
          e.target &&
          e.target.nodeName == "SPAN" &&
          e.target.id == "delete-row-icon"
        ) {
          var deleteBtns = tbody.querySelectorAll("#delete-row-icon");
          deleteBtns = Array.from(deleteBtns);
          var rows = tbody.querySelectorAll("#status-tab tbody > tr");
          rows = Array.from(rows);
          rows[Array.from(deleteBtns).indexOf(e.target)].remove();
        }
      });
    }

    addControlButtonListeners() {
      var tbody = document.querySelector("#status-tab tbody");
      tbody.addEventListener("click", e => {
        if (
          e.target.matches(".control--select--list--item-inner") &&
          e.target.parentElement.parentElement.nextElementSibling.classList.contains(
            "entity-type-button"
          )
        ) {
          var allControlButtons = tbody.querySelectorAll(
            "button.entity-type-button"
          );
          var rows = Array.from(tbody.querySelectorAll("tr"));
          var row = rows.find(row => row.contains(e.target));
          var index = rows.indexOf(row);
          var company = rows[index].querySelector("td#status-company-field");
          var contact = rows[index].querySelector("td#status-contact-field");
          var button = e.target.parentElement.parentElement.nextElementSibling;
          switch (button.dataset.value) {
            case "company":
              company.style.display = "table-cell";
              contact.style.display = "none";
              break;
            case "contact":
              contact.style.display = "table-cell";
              company.style.display = "none";
              break;
          }
        }
      });
    }

    addTabButtonsListeners() {
      var tabBtns = document.querySelectorAll("[data-content-selector]");
      var tabs = document.querySelectorAll("[data-content-tab]");
      tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
          const target = document.querySelector(btn.dataset.contentSelector);
          tabs.forEach(tab => {
            tab.classList.remove("active");
          });
          tabBtns.forEach(btn => btn.classList.remove("active"));
          target.classList.add("active");
          btn.classList.add("active");
        });
      });
    }

    renderStatusTab(callback) {
      // const statusTab = document.querySelector("#status-tab");
      const { dependencyItems, entityItems, companyItems, contactItems } =
        this.returnItems();
      var statusTab = $("#status-tab");
      this.getTemplate("status-tab")
        .then(statusTemplate => {
          return statusTemplate.render({
            statusDependencyTypeOptions: dependencyItems,
            statusEntityTypeOptions: entityItems,
            statusCompanyFieldOptions: companyItems,
            statusContactFieldOptions: contactItems,
          });
        })
        .then(result => {
          statusTab.append($(result));
          callback();
        });
    }

    renderTableRow(callback) {
      var tableBody = $("#status-tbody");
      const { dependencyItems, entityItems, companyItems, contactItems } =
        this.returnItems();
      this.getTemplate("table-row")
        .then(rowTemplate => {
          return rowTemplate.render({
            statusDependencyTypeOptions: dependencyItems,
            statusEntityTypeOptions: entityItems,
            statusCompanyFieldOptions: companyItems,
            statusContactFieldOptions: contactItems,
          });
        })
        .then(result => {
          tableBody.append($(result));
          // callback();
        });
    }

    renderContactTab() {
      const { contactItems, leadItems } = this.returnItems();
      const contactTab = $("#contact-tab");
      this.getTemplate("contact-tab")
        .then(contactTemplate =>
          contactTemplate.render({
            contactFieldOptions: contactItems,
            contactLeadFieldOptions: leadItems,
          })
        )
        .then(result => contactTab.append($(result)));
    }

    renderCompanyTab() {
      const { companyItems, leadItems } = this.returnItems();
      const companyTab = $("#company-tab");
      this.getTemplate("company-tab")
        .then(companyTemplate =>
          $(
            companyTemplate.render({
              companyFieldOptions: companyItems,
              companyLeadFieldOptions: leadItems,
            })
          )
        )
        .then(result => companyTab.append(result));
    }

    renderSkeleton(callback) {
      this.getTemplate("entirety").then(entireTemplate => {
        let $page = $("#work_area");
        $page.append($(entireTemplate.render()));
        callback();
      });
    }

    renderPage() {
      this.makeRequest({
        method: "get",
        path: "widget-request",
        successful: response => {
          this.companyFields = response["companyFields"];
          this.contactFields = response["contactFields"];
          this.leadFields = response["leadFields"];
          this.renderSkeleton(() => {
            this.addTabButtonsListeners();
            const { companyItems, contactItems, dependencyItems, entityItems } =
              this.returnItems();
            this.renderContactTab();
            this.renderStatusTab(() => {
              var addRowBtn = document.querySelector("#addRow");
              addRowBtn.addEventListener("click", () => {
                this.renderTableRow(
                  dependencyItems,
                  entityItems,
                  companyItems,
                  contactItems
                );
              });
              this.addDeleteButtonListeners();
              this.addControlButtonListeners();
            });
            this.renderCompanyTab();
          });
        },
      });
    }

    destroy() {
      this.isDestroyed = true;
    }
  }

  return function () {
    let self = this;
    let widget = new Widget(this, templatesRenderer(this));
    // var getTemplate = templatesRenderer(this);
    this.callbacks = {
      init: function () {
        var settings = self.get_settings();
        var styles = [
          "style.css",
          "status-tab.css",
          "contact-tab.css",
          "company-tab.css",
        ];
        styles.forEach(style => {
          $("head").append(
            '<link href="' +
              settings.path +
              "/" +
              style +
              "?v=" +
              settings.version +
              '" type="text/css" rel="stylesheet">'
          );
        });
        return true;
      },
      advancedSettings: function () {
        widget.renderPage();
        return true;
      },
      render: () => true,
      bind_actions: function () {
        return true;
      },
      destroy: () => widget.destroy(),
      onSave: () => true,
    };
    return this;
  };
});
