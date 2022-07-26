var data = {
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

      this.companyNumericFields = [];
      this.companyStringFields = [];
      this.contactNumericFields = [];
      this.contactStringFields = [];
      this.leadFields = [];
      this.dependencyTypes = data["dependencyTypes"];
      this.entityTypes = data["entityTypes"];
    }

    makeRequest({ method, path, data, successful, complete } = {}) {
      // alert(`${this.widget.get_settings().serverURL}${path}`);
      this.widget.$authorizedAjax({
        url: `${this.widget.get_settings().serverURL}${path}`,
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
      const companyStringItems = this.optionsToItems({
        options: this.companyStringFields,
      });
      const companyNumericItems = this.optionsToItems({
        options: this.companyNumericFields,
      });
      const leadItems = this.optionsToItems({ options: this.leadFields });
      const contactStringItems = this.optionsToItems({
        options: this.contactStringFields,
      });
      const contactNumericItems = this.optionsToItems({
        options: this.contactNumericFields,
      });
      const dependencyItems = this.optionsToItems({
        options: this.dependencyTypes,
      });
      const entityItems = this.optionsToItems({ options: this.entityTypes });
      return {
        companyStringItems,
        companyNumericItems,
        leadItems,
        contactStringItems,
        contactNumericItems,
        dependencyItems,
        entityItems,
      };
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

    addTestRequestButtonListener() {
      var testBtn = document.querySelector("#test-request");
      testBtn.addEventListener("click", () => {
        this.makeRequest({
          method: "get",
          path: "settings/run-company-check",
          successful: response => {
            alert(JSON.stringify(response));
            console.log(response);
          },
        });
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

    addContactTabButtonListeners() {
      var saveButton = document.querySelector("#contact-tab #save");
      var runCheck = document.querySelector("#contact-tab #runCheck");
      var contactMonths = document.querySelector(
        "#contact-tab input[name=contact_input_months]"
      );
      var contactSelect = document.querySelector(
        "#contact-tab input[name=contact_select_field]"
      );
      var contactSelectLead = document.querySelector(
        "#contact-tab input[name=contact_select_lead_field]"
      );
      saveButton.addEventListener("click", () => {
        var months = contactMonths.value;
        var contactField = contactSelect.value;
        var leadField = contactSelectLead.value;
        // alert(months + " " + contactField + " " + leadField);
        if (!Number.isInteger(parseFloat(months))) {
          AMOCRM.notifications.show_message({
            header: this.widget.langs.widget.name,
            text: "Кол-во мес. должно быть целым числом",
          });
          return;
        }
        this.makeRequest({
          method: "post",
          path: "settings/contact",
          data: {
            months: parseInt(months),
            lead_field_id: leadField,
            contact_field_id: contactField,
          },
          successful: response => {
            // alert(JSON.stringify(response));
            // console.log(response);
          },
        });
      });
      runCheck.addEventListener("click", () => {
        this.makeRequest({
          method: "post",
          path: "settings/run-contact-check",
          successful: response => {
            // alert(JSON.stringify(response));
            // console.log(response);
          },
        });
      });
    }

    addCompanyTabButtonListeners() {
      var saveButton = document.querySelector("#company-tab #save");
      var runCheck = document.querySelector("#company-tab #runCheck");
      var companyMonths = document.querySelector(
        "#company-tab input[name=company_input_months]"
      );
      var companySelect = document.querySelector(
        "#company-tab input[name=company_select_field]"
      );
      var companySelectLead = document.querySelector(
        "#company-tab input[name=company_select_lead_field]"
      );
      saveButton.addEventListener("click", () => {
        var months = companyMonths.value;
        var companyField = companySelect.value;
        var leadField = companySelectLead.value;
        // alert(months + " " + companyField + " " + leadField);
        if (!Number.isInteger(parseFloat(months))) {
          AMOCRM.notifications.show_message({
            header: this.widget.langs.widget.name,
            text: "Кол-во мес. должно быть целым числом",
          });
          return;
        }
        this.makeRequest({
          method: "post",
          path: "settings/company",
          data: {
            months: parseInt(months),
            lead_field_id: leadField,
            company_field_id: companyField,
          },
          successful: response => {
            // alert(JSON.stringify(response));
            // console.log(response);
          },
        });
      });
      runCheck.addEventListener("click", () => {
        this.makeRequest({
          method: "post",
          path: "settings/run-company-check",
          successful: response => {
            // alert(JSON.stringify(response));
            // console.log(response);
          },
        });
      });
    }

    addStatusTabButtonListeners() {
      const { dependencyItems, entityItems, companyItems, contactItems } =
        this.returnItems();
      var addRowBtn = document.querySelector("#addRow");
      var saveBtn = document.querySelector("#status-tab #save");
      addRowBtn.addEventListener("click", () => {
        this.renderTableRow(
          dependencyItems,
          entityItems,
          companyItems,
          contactItems
        );
      });
      saveBtn.addEventListener("click", () => {
        var rows = document.querySelectorAll("#status-tab tbody tr");
        var rowsArray = Array.from(rows);
        var result = rowsArray.map(row => {
          var status = row.querySelector("input[name=status_input]");
          var depType = row.querySelector(
            "input[name=status_select_dependency_type]"
          );
          var entityType = row.querySelector(
            "input[name=status_select_entity_type]"
          );
          var entityField = row.querySelector(
            `input[name=status_select_entity_${entityType.value}_field]`
          );
          var fromAmount = row.querySelector("input[name=status_input_from]");
          var toAmount = row.querySelector("input[name=status_input_to]");
          if (!status.value) {
            AMOCRM.notifications.show_message({
              header: this.widget.langs.widget.name,
              text: "Поле статус не должно быть пустым",
            });
            return null;
          }
          if (!fromAmount.value) {
            AMOCRM.notifications.show_message({
              header: this.widget.langs.widget.name,
              text: 'Правило "от" не должно быть пустым',
            });
            return null;
          }
          if (!toAmount.value) {
            AMOCRM.notifications.show_message({
              header: this.widget.langs.widget.name,
              text: 'Правило "до" не должно быть пустым',
            });
            return null;
          }
          if (!(parseInt(fromAmount.value) <= parseInt(toAmount.value))) {
            AMOCRM.notifications.show_message({
              header: this.widget.langs.widget.name,
              text: 'Значение "от" больше значения "до"',
            });
            return null;
          }
          return {
            status: status.value,
            dependency_type: depType.value,
            entity_type: entityType.value,
            field_id: entityField.value,
            from_amount: fromAmount.value,
            to_amount: toAmount.value,
          };
        });

        if (result.indexOf(null) == -1) {
          this.makeRequest({
            method: "post",
            path: "settings/status",
            data: result,
            successful: response => {
              alert(JSON.stringify(response));
              console.log(response);
            },
          });
        }
      });
      this.addDeleteButtonListeners();
      this.addControlButtonListeners();
    }

    renderStatusTab(callback) {
      var statusTab = $("#status-tab");
      this.requestSavedStatusSettings().then(settings => {
        this.getTemplate("status-tab")
          .then(statusTemplate => {
            return statusTemplate.render();
          })
          .then(result => {
            statusTab.append($(result));
            if (settings.length > 0) {
              settings.forEach(setting => {
                const {
                  status: statusValue,
                  dependency_type: depTypeSelected,
                  entity_type: entityTypeSelected,
                  field_id: contactFieldSelected,
                  field_id: companyFieldSelected,
                  from_amount: fromValue,
                  to_amount: toValue,
                } = setting;
                this.renderTableRow({
                  statusValue: statusValue,
                  depTypeSelected: depTypeSelected,
                  entityTypeSelected: entityTypeSelected,
                  contactFieldSelected: contactFieldSelected,
                  companyFieldSelected: companyFieldSelected,
                  fromValue: fromValue,
                  toValue: toValue,
                });
              });
            } else {
              this.renderTableRow();
            }

            callback();
          });
      });
    }

    renderTableRow(data = {}) {
      var tableBody = $("#status-tbody");
      const {
        dependencyItems,
        entityItems,
        companyStringItems,
        contactStringItems,
      } = this.returnItems();
      this.getTemplate("table-row")
        .then(rowTemplate => {
          return rowTemplate.render({
            statusDependencyTypeOptions: dependencyItems,
            statusEntityTypeOptions: entityItems,
            statusCompanyFieldOptions: companyStringItems,
            statusContactFieldOptions: contactStringItems,
            ...data,
          });
        })
        .then(result => {
          tableBody.append($(result));
        });
    }

    renderContactTab(callback) {
      const { contactNumericItems, leadItems } = this.returnItems();
      const contactTab = $("#contact-tab");
      this.requestSavedContactSettings().then(settings => {
        try {
          const selectedContactField = settings["contact_field_id"];
          const selectedLeadField = settings["lead_field_id"];
          const months = settings["months"];
          var values = { selectedContactField, selectedLeadField, months };
        } catch (error) {
          var values = {};
        }
        this.getTemplate("contact-tab")
          .then(contactTemplate =>
            contactTemplate.render({
              contactFieldOptions: contactNumericItems,
              contactLeadFieldOptions: leadItems,
              ...values,
            })
          )
          .then(result => {
            contactTab.append($(result));
            callback();
          });
      });
    }

    renderCompanyTab(callback) {
      const { companyNumericItems, leadItems } = this.returnItems();
      const companyTab = $("#company-tab");
      this.requestSavedCompanySettings().then(settings => {
        try {
          const selectedCompanyField = settings["company_field_id"];
          const selectedLeadField = settings["lead_field_id"];
          const months = settings["months"];
          var values = { selectedCompanyField, selectedLeadField, months };
        } catch (error) {
          // alert(error);
          var values = {};
        }
        this.getTemplate("company-tab")
          .then(companyTemplate =>
            $(
              companyTemplate.render({
                companyFieldOptions: companyNumericItems,
                companyLeadFieldOptions: leadItems,
                ...values,
              })
            )
          )
          .then(result => {
            companyTab.append(result);
            callback();
          });
      });
    }

    renderSkeleton(callback) {
      let $page = $("#work_area");
      this.getTemplate("entirety").then(entireTemplate => {
        $page.append($(entireTemplate.render()));
        callback();
      });
    }

    requestSavedContactSettings() {
      const request = new Promise((resolve, reject) => {
        this.makeRequest({
          method: "get",
          path: "settings/contact",
          successful: response => {
            // alert(JSON.stringify(response));
            resolve(response);
          },
        });
      });
      return request;
    }

    requestSavedCompanySettings() {
      const request = new Promise((resolve, reject) => {
        this.makeRequest({
          method: "get",
          path: "settings/company",
          successful: response => {
            // alert(JSON.stringify(response));
            resolve(response);
          },
        });
      });
      return request;
    }

    requestSavedStatusSettings() {
      const request = new Promise((resolve, reject) => {
        this.makeRequest({
          method: "get",
          path: "settings/status",
          successful: response => {
            // alert(JSON.stringify(response));
            resolve(response);
          },
        });
      });
      return request;
    }

    requestSavedSettings() {
      return Promise.all([
        this.requestSavedContactSettings(),
        this.requestSavedCompanySettings(),
        this.requestSavedStatusSettings(),
      ]);
    }

    addLoadingIcon() {
      let $page = $("#work_area");
      var loading = document.createElement("span");
      loading.classList.add("loading-icon");
      $page.append(loading);
    }

    removeLoadingIcon() {
      var loading = document.querySelector("span.loading-icon");
      loading.style.display = "none";
    }

    renderPage() {
      this.addLoadingIcon();
      this.makeRequest({
        method: "get",
        path: "settings/get-custom-fields",
        successful: response => {
          // this.companyFields = response["companyFields"];
          // this.contactFields = response["contactFields"];
          // alert(JSON.stringify(response));
          this.leadFields = response["leadFields"];

          //TODO:
          this.companyStringFields = response["companyStringFields"];
          this.companyNumericFields = response["companyNumericFields"];
          this.contactStringFields = response["contactStringFields"];
          this.contactNumericFields = response["contactNumericFields"];

          this.renderSkeleton(() => {
            this.removeLoadingIcon();
            this.addTabButtonsListeners();
            // this.addTestRequestButtonListener();
            this.renderContactTab(() => this.addContactTabButtonListeners());
            this.renderCompanyTab(() => this.addCompanyTabButtonListeners());
            this.renderStatusTab(() => this.addStatusTabButtonListeners());
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
              "/styles/" +
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
