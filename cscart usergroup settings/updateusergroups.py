# vibe coded with Gemini 2.5 pro

from auDAOlib import readWEB, updateWEB
from credentials import MYLOCALPATH
from pandas import read_excel

def modify_product_usergroups(product_codes, usergroup_id, action):
	"""
	Adds or removes a usergroup for a list of products in a CS-Cart database
	while preserving other usergroup assignments.

	Args:
		product_ids (list): A list of integer product IDs to update.
		usergroup_id (int): The integer ID of the usergroup to add or remove.
		action (str): Either 'add' or 'remove'.
	"""
	if not product_codes:
		print("No product IDs provided. Exiting.")
		return

	try:

		# Build the SELECT query to fetch only the products we need to modify
		product_codes_str = ', '.join(f"'{code}'" for code in product_codes)
		select_query = f"SELECT product_id, usergroup_ids FROM cscart_products WHERE product_code IN ({product_codes_str})"

		productsDF= readWEB(select_query)
		products_to_update = productsDF.to_dict(orient='records')

		update_count = 0
		total_products = len(products_to_update)
		for idx, product in enumerate(products_to_update, start=1):
			current_ids_str = product.get('usergroup_ids', '') or '' # Handle None and empty strings
			
			# Convert comma-separated string to a set for easy manipulation
			id_set = set(current_ids_str.split(','))
			id_set.discard('') # Remove any empty elements that can result from split()

			original_set_size = len(id_set)
			
			# --- The Core Logic: Add or Remove ---
			if action == 'add':
				id_set.add(str(usergroup_id))
			elif action == 'remove':
				id_set.discard(str(usergroup_id))
			
			# Only update if a change actually happened
			if len(id_set) != original_set_size or action == 'add' and original_set_size == 0:
				new_ids_str = ','.join(sorted(list(id_set), key=int))
				update_query = '''UPDATE cscart_products SET usergroup_ids = :new_ids WHERE product_id = :productid'''
				updateWEB(update_query, {'new_ids': new_ids_str, 'productid':product['product_id']})
				update_count += 1
				print(f"Updated {update_count}/{total_products} products...", end='\r')

		print(f"\nOperation '{action}' for usergroup '{usergroup_id}' complete.")
		print(f"Successfully modified and updated {update_count} product(s).")

	except Exception as err:
		print(f"An error occurred: {err}")
		return


if __name__ == '__main__':


	# AU usergroup IDs: 8=PIREX, 12=PATRIA, 14=SPAR, 15=EXPORT_MIRA, 16=Export PetrDanek, 17=Export egyéb

	USERGROUP = 15

	listapath = MYLOCALPATH+r'\OneDrive\Python\cscart usergroup settings\cikklista.xlsx' 
	lista=read_excel(listapath, usecols='A:A', dtype={'itemcode': str})['itemcode'].tolist()
	
	current_products_query = f"""
		SELECT product_code
		FROM cscart_products
		WHERE find_in_set('{USERGROUP}', usergroup_ids)
	"""
	current_products = readWEB(current_products_query)['product_code'].tolist()

	add_list = list(set(lista) - set(current_products))
	remove_list = list(set(current_products) - set(lista))

	modify_product_usergroups(add_list, USERGROUP, 'add')
	modify_product_usergroups(remove_list, USERGROUP, 'remove')

	print("\n" + "="*30 + "\n")
