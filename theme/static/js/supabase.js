const SUPABASE_URL = 'https://wvrzfalrgvepxfgwekuj.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2cnpmYWxyZ3ZlcHhmZ3dla3VqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzcyNjk1MTIsImV4cCI6MjA5Mjg0NTUxMn0.0W1bMeNujiZNTqiQ_h798SbVVT4PS4b_O6SeEp3UVFc'

const { createClient } = supabase
const supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

async function fetchTable(tableName, options = {}) {
	const columns = options.columns || '*'
	const query = supabaseClient.from(tableName).select(columns)

	if (options.orderBy) {
		query.order(options.orderBy.column, { ascending: options.orderBy.ascending ?? true })
	}

	if (options.limit) {
		query.limit(options.limit)
	}

	const { data, error } = await query

	if (error) {
		throw error
	}

	return data
}

async function populateSelectFromTable(selectElement) {
	if (!selectElement) {
		return
	}

	const tableName = selectElement.dataset.supabaseTable
	if (!tableName) {
		return
	}

	const valueField = selectElement.dataset.valueField || 'value'
	const labelField = selectElement.dataset.labelField || 'label'

	const rows = await fetchTable(tableName, {
		columns: `${valueField}, ${labelField}`,
		orderBy: { column: labelField, ascending: true },
	})

	rows.forEach((row) => {
		const option = document.createElement('option')
		option.value = row[valueField]
		option.textContent = row[labelField]
		selectElement.appendChild(option)
	})
}

async function populateSelects(root = document) {
	const selects = root.querySelectorAll('select[data-supabase-table]')
	for (const selectElement of selects) {
		try {
			await populateSelectFromTable(selectElement)
		} catch (error) {
			console.error(`Failed to load ${selectElement.dataset.supabaseTable}:`, error)
		}
	}
}

window.AeroMilesSupabase = {
	client: supabaseClient,
	fetchTable,
	populateSelectFromTable,
	populateSelects,
}

window.addEventListener('DOMContentLoaded', () => {
	window.AeroMilesSupabase.populateSelects()
})
